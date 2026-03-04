from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np
import ray
import torch
from torch import nn
from torch.optim.lr_scheduler import CosineAnnealingLR

from tetris_rl.env.tetris_env import RewardConfig, TetrisEnv
from tetris_rl.model.ppo_model import ActorCritic
from tetris_rl.trainer.ray_workers import RolloutWorker, WorkerConfig


@dataclass(frozen=True, slots=True)
class PPOConfig:
    seed: int = 0
    max_actions: int = 64
    workers: int = 4
    rollout_steps_per_worker: int = 512
    update_epochs: int = 4
    minibatch_size: int = 1024
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_coef: float = 0.2
    ent_coef: float = 0.01
    target_entropy: float = -1.0  # Target for adaptive entropy (negative = use fixed)
    adaptive_entropy: bool = True  # Enable adaptive entropy coefficient
    ent_coef_lr: float = 1e-3  # Learning rate for entropy coefficient
    vf_coef: float = 0.5
    lr: float = 3e-4
    lr_schedule: bool = True  # Use cosine annealing for learning rate
    max_grad_norm: float = 0.5
    total_updates: int = 10_000
    eval_interval: int = 25
    eval_episodes: int = 5  # Number of episodes for evaluation
    checkpoint_interval: int = 50
    out_dir: str = "runs/tetris_ppo"
    reward: RewardConfig = RewardConfig()
    target_kl: float = 0.015  # KL divergence early stopping threshold (0 = disabled)
    use_tensorboard: bool = True  # Enable TensorBoard logging


@dataclass(slots=True)
class EvalStats:
    mean_score: float
    std_score: float
    max_score: float
    mean_lines: float
    mean_duration: float


def _setup_logger(out_dir: Path) -> logging.Logger:
    out_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("tetris_rl")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh = logging.FileHandler(out_dir / "train.log", encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def _set_seeds(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def _gae(
    rewards: np.ndarray,
    dones: np.ndarray,
    values: np.ndarray,
    last_value: float,
    gamma: float,
    gae_lambda: float,
) -> tuple[np.ndarray, np.ndarray]:
    T = rewards.shape[0]
    adv = np.zeros((T,), dtype=np.float32)
    last_gae = 0.0
    for t in reversed(range(T)):
        next_non_terminal = 1.0 - float(dones[t])
        next_value = last_value if t == T - 1 else float(values[t + 1])
        delta = float(rewards[t]) + gamma * next_value * next_non_terminal - float(values[t])
        last_gae = delta + gamma * gae_lambda * next_non_terminal * last_gae
        adv[t] = float(last_gae)
    ret = adv + values.astype(np.float32, copy=False)
    return adv, ret


class PPOTrainer:
    def __init__(self, cfg: PPOConfig) -> None:
        self.cfg = cfg
        self.out_dir = Path(cfg.out_dir)
        self.logger = _setup_logger(self.out_dir)

        _set_seeds(cfg.seed)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.eval_env = TetrisEnv(seed=cfg.seed + 123, reward=cfg.reward, max_actions=cfg.max_actions)
        obs_dim = int(self.eval_env.observation_space.shape[0])
        act_dim = int(self.eval_env.action_space.n)

        self.model = ActorCritic(obs_dim=obs_dim, act_dim=act_dim).to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=cfg.lr, eps=1e-5)

        # Learning rate scheduler
        self.scheduler: Any = None
        if cfg.lr_schedule:
            self.scheduler = CosineAnnealingLR(
                self.optimizer, T_max=cfg.total_updates, eta_min=cfg.lr * 0.1
            )

        # Adaptive entropy coefficient
        self.log_ent_coef: torch.Tensor | None = None
        self.ent_optimizer: Any = None
        if cfg.adaptive_entropy and cfg.target_entropy > 0:
            self.log_ent_coef = torch.log(torch.tensor([cfg.ent_coef], device=self.device))
            self.ent_optimizer = torch.optim.Adam([self.log_ent_coef], lr=cfg.ent_coef_lr)

        # TensorBoard writer (lazy import)
        self.tb_writer: Any = None
        if cfg.use_tensorboard:
            try:
                from torch.utils.tensorboard import SummaryWriter
                self.tb_writer = SummaryWriter(log_dir=str(self.out_dir / "tensorboard"))
            except ImportError:
                self.logger.warning("TensorBoard not available, skipping logging")

        self._workers: list[Any] = []

        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
        with (self.out_dir / "config.json").open("w", encoding="utf-8") as f:
            json.dump(cfg.__dict__, f, ensure_ascii=False, indent=2)

    def start_ray(self) -> None:
        if ray.is_initialized():
            return
        ray.init(ignore_reinit_error=True, include_dashboard=False, log_to_driver=False)

    def stop_ray(self) -> None:
        if ray.is_initialized():
            ray.shutdown()

    def start_workers(self) -> None:
        self.start_ray()
        obs_dim = int(self.eval_env.observation_space.shape[0])
        act_dim = int(self.eval_env.action_space.n)
        cfg = WorkerConfig(seed=self.cfg.seed, max_actions=self.cfg.max_actions, reward=self.cfg.reward)
        self._workers = [RolloutWorker.remote(obs_dim, act_dim, cfg, i) for i in range(self.cfg.workers)]
        state = {k: v.cpu() for k, v in self.model.state_dict().items()}
        ray.get([w.set_weights.remote(state) for w in self._workers])

    def stop_workers(self) -> None:
        if not self._workers:
            return
        for w in self._workers:
            try:
                ray.kill(w)
            except Exception:
                pass
        self._workers = []

    def save_checkpoint(self, tag: str) -> Path:
        ckpt = {
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "scheduler": self.scheduler.state_dict() if self.scheduler else None,
            "cfg": self.cfg.__dict__,
        }
        if self.log_ent_coef is not None:
            ckpt["log_ent_coef"] = self.log_ent_coef.item()
        path = self.out_dir / "checkpoints" / f"{tag}.pt"
        torch.save(ckpt, path)
        return path

    def load_checkpoint(self, path: str | Path) -> None:
        ckpt = torch.load(Path(path), map_location=self.device)
        self.model.load_state_dict(ckpt["model"])
        if "optimizer" in ckpt:
            self.optimizer.load_state_dict(ckpt["optimizer"])
        if "scheduler" in ckpt and ckpt["scheduler"] is not None and self.scheduler:
            self.scheduler.load_state_dict(ckpt["scheduler"])
        if "log_ent_coef" in ckpt and self.log_ent_coef is not None:
            self.log_ent_coef.data = torch.tensor([ckpt["log_ent_coef"]], device=self.device)

    @torch.no_grad()
    def evaluate(self, episodes: int = 1) -> EvalStats:
        """Evaluate the current policy over multiple episodes."""
        scores: list[float] = []
        lines_cleared: list[int] = []
        durations: list[float] = []

        for _ in range(int(episodes)):
            obs, info = self.eval_env.reset()
            done = False
            steps = 0
            start_time = time.time()
            while not done:
                mask = info["action_mask"]
                a, _logp, _v = self.model.act(obs, mask, device=self.device, deterministic=True)
                obs, _r, terminated, _truncated, info = self.eval_env.step(a)
                done = bool(terminated)
                steps += 1
            duration = time.time() - start_time
            scores.append(float(info.get("score", 0.0)))
            lines_cleared.append(int(info.get("lines_cleared", 0)))
            durations.append(duration)

        return EvalStats(
            mean_score=float(np.mean(scores)) if scores else 0.0,
            std_score=float(np.std(scores)) if len(scores) > 1 else 0.0,
            max_score=float(np.max(scores)) if scores else 0.0,
            mean_lines=float(np.mean(lines_cleared)) if lines_cleared else 0.0,
            mean_duration=float(np.mean(durations)) if durations else 0.0,
        )

    def _collect_batch(self) -> dict[str, np.ndarray]:
        if not self._workers:
            self.start_workers()
        state = {k: v.detach().cpu() for k, v in self.model.state_dict().items()}
        ray.get([w.set_weights.remote(state) for w in self._workers])

        futures = [w.rollout.remote(self.cfg.rollout_steps_per_worker) for w in self._workers]
        batches = ray.get(futures)

        obs_list: list[np.ndarray] = []
        act_list: list[np.ndarray] = []
        logp_list: list[np.ndarray] = []
        val_list: list[np.ndarray] = []
        ret_list: list[np.ndarray] = []
        adv_list: list[np.ndarray] = []
        done_list: list[np.ndarray] = []
        mask_list: list[np.ndarray] = []
        ep_scores: list[float] = []

        for b in batches:
            obs = b["obs"]
            actions = b["actions"]
            logp = b["logprobs"]
            values = b["values"]
            rewards = b["rewards"]
            dones = b["dones"]
            action_masks = b["action_masks"]
            last_value = float(b["last_value"])

            adv, ret = _gae(rewards, dones, values, last_value, self.cfg.gamma, self.cfg.gae_lambda)

            obs_list.append(obs)
            act_list.append(actions)
            logp_list.append(logp)
            val_list.append(values)
            ret_list.append(ret)
            adv_list.append(adv)
            done_list.append(dones)
            mask_list.append(action_masks)

            if "episode_scores" in b and len(b["episode_scores"]) > 0:
                ep_scores.extend([float(x) for x in b["episode_scores"].tolist()])

        batch = {
            "obs": np.concatenate(obs_list, axis=0),
            "actions": np.concatenate(act_list, axis=0),
            "logprobs": np.concatenate(logp_list, axis=0),
            "values": np.concatenate(val_list, axis=0),
            "returns": np.concatenate(ret_list, axis=0),
            "advantages": np.concatenate(adv_list, axis=0),
            "dones": np.concatenate(done_list, axis=0),
            "action_masks": np.concatenate(mask_list, axis=0),
            "episode_scores": np.array(ep_scores, dtype=np.float32),
        }
        return batch

    def update(self, batch: dict[str, np.ndarray]) -> dict[str, float]:
        obs = torch.as_tensor(batch["obs"], dtype=torch.float32, device=self.device)
        actions = torch.as_tensor(batch["actions"], dtype=torch.int64, device=self.device)
        old_logprobs = torch.as_tensor(batch["logprobs"], dtype=torch.float32, device=self.device)
        returns = torch.as_tensor(batch["returns"], dtype=torch.float32, device=self.device)
        advantages = torch.as_tensor(batch["advantages"], dtype=torch.float32, device=self.device)
        action_masks = torch.as_tensor(batch["action_masks"], dtype=torch.float32, device=self.device)

        advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-8)

        batch_size = obs.shape[0]
        inds = np.arange(batch_size)

        clipfracs: list[float] = []
        policy_losses: list[float] = []
        value_losses: list[float] = []
        entropies: list[float] = []
        approx_kls: list[float] = []
        current_ent_coef = self.cfg.ent_coef

        for epoch in range(self.cfg.update_epochs):
            np.random.shuffle(inds)
            for start in range(0, batch_size, self.cfg.minibatch_size):
                mb_inds = inds[start : start + self.cfg.minibatch_size]
                mb_obs = obs[mb_inds]
                mb_actions = actions[mb_inds]
                mb_old_logp = old_logprobs[mb_inds]
                mb_returns = returns[mb_inds]
                mb_adv = advantages[mb_inds]
                mb_masks = action_masks[mb_inds]

                # Update entropy coefficient if adaptive
                if self.log_ent_coef is not None and self.ent_optimizer is not None:
                    new_logp, entropy, new_value = self.model.evaluate_actions(mb_obs, mb_actions, mb_masks)
                    ent_coef_loss = -(self.log_ent_coef * (entropy + self.cfg.target_entropy)).mean()
                    self.ent_optimizer.zero_grad()
                    ent_coef_loss.backward()
                    self.ent_optimizer.step()
                    current_ent_coef = torch.exp(self.log_ent_coef).item()

                new_logp, entropy, new_value = self.model.evaluate_actions(mb_obs, mb_actions, mb_masks)
                log_ratio = new_logp - mb_old_logp
                ratio = log_ratio.exp()

                with torch.no_grad():
                    approx_kl = (mb_old_logp - new_logp).mean()
                    clipfrac = ((ratio - 1.0).abs() > self.cfg.clip_coef).float().mean()
                    approx_kls.append(float(approx_kl.item()))
                    clipfracs.append(float(clipfrac.item()))

                pg_loss1 = -mb_adv * ratio
                pg_loss2 = -mb_adv * torch.clamp(ratio, 1.0 - self.cfg.clip_coef, 1.0 + self.cfg.clip_coef)
                pg_loss = torch.max(pg_loss1, pg_loss2).mean()

                v_loss = 0.5 * ((new_value - mb_returns) ** 2).mean()
                ent = entropy.mean()

                loss = pg_loss + self.cfg.vf_coef * v_loss - current_ent_coef * ent

                self.optimizer.zero_grad(set_to_none=True)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.max_grad_norm)
                self.optimizer.step()

                policy_losses.append(float(pg_loss.item()))
                value_losses.append(float(v_loss.item()))
                entropies.append(float(ent.item()))

            # Early stopping based on KL divergence
            if self.cfg.target_kl > 0:
                mean_approx_kl = float(np.mean(approx_kls[-len(batch_size) // self.cfg.minibatch_size:]))
                if mean_approx_kl > self.cfg.target_kl:
                    self.logger.info("Early stopping due to high KL divergence: %.4f", mean_approx_kl)
                    break

        # Step the learning rate scheduler
        if self.scheduler is not None:
            self.scheduler.step()
            current_lr = self.scheduler.get_last_lr()[0]
        else:
            current_lr = self.cfg.lr

        metrics = {
            "loss_policy": float(np.mean(policy_losses)) if policy_losses else 0.0,
            "loss_value": float(np.mean(value_losses)) if value_losses else 0.0,
            "entropy": float(np.mean(entropies)) if entropies else 0.0,
            "ent_coef": current_ent_coef,
            "approx_kl": float(np.mean(approx_kls)) if approx_kls else 0.0,
            "clipfrac": float(np.mean(clipfracs)) if clipfracs else 0.0,
            "learning_rate": current_lr,
        }
        return metrics

    def _log_to_tensorboard(self, update_idx: int, metrics: dict[str, float], eval_stats: EvalStats | None = None) -> None:
        if self.tb_writer is None:
            return

        for k, v in metrics.items():
            self.tb_writer.add_scalar(f"train/{k}", v, update_idx)

        if eval_stats is not None:
            self.tb_writer.add_scalar("eval/mean_score", eval_stats.mean_score, update_idx)
            self.tb_writer.add_scalar("eval/std_score", eval_stats.std_score, update_idx)
            self.tb_writer.add_scalar("eval/max_score", eval_stats.max_score, update_idx)
            self.tb_writer.add_scalar("eval/mean_lines", eval_stats.mean_lines, update_idx)
            self.tb_writer.add_scalar("eval/mean_duration", eval_stats.mean_duration, update_idx)

        self.tb_writer.flush()

    def train(
        self,
        stop_flag: Callable[[], bool],
        on_update: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> None:
        self.start_workers()
        start_time = time.time()
        for update_idx in range(1, self.cfg.total_updates + 1):
            if stop_flag():
                break

            batch = self._collect_batch()
            metrics = self.update(batch)

            mean_ep_score = float(np.mean(batch["episode_scores"])) if len(batch["episode_scores"]) > 0 else 0.0

            payload: dict[str, Any] = {
                "update": update_idx,
                "steps": int(update_idx * self.cfg.workers * self.cfg.rollout_steps_per_worker),
                "mean_episode_score": mean_ep_score,
                "elapsed_s": float(time.time() - start_time),
                **metrics,
            }

            eval_stats: EvalStats | None = None
            if update_idx % self.cfg.eval_interval == 0:
                eval_stats = self.evaluate(episodes=self.cfg.eval_episodes)
                payload["eval_mean_score"] = eval_stats.mean_score
                payload["eval_std_score"] = eval_stats.std_score
                payload["eval_max_score"] = eval_stats.max_score
                payload["eval_mean_lines"] = eval_stats.mean_lines
                self.logger.info(
                    "Eval: mean=%.1f std=%.1f max=%.1f lines=%.1f",
                    eval_stats.mean_score,
                    eval_stats.std_score,
                    eval_stats.max_score,
                    eval_stats.mean_lines,
                )

            if update_idx % self.cfg.checkpoint_interval == 0:
                ckpt_path = self.save_checkpoint(tag=f"update_{update_idx:07d}")
                payload["checkpoint"] = str(ckpt_path)

            # Log to TensorBoard
            self._log_to_tensorboard(update_idx, metrics, eval_stats)

            self.logger.info(
                "upd=%d steps=%d score=%.1f lp=%.4f lv=%.4f ent=%.4f kl=%.4f lr=%.6f",
                payload["update"],
                payload["steps"],
                payload["mean_episode_score"],
                payload["loss_policy"],
                payload["loss_value"],
                payload["entropy"],
                payload["approx_kl"],
                payload["learning_rate"],
            )

            if on_update is not None:
                on_update(payload)

        # Close TensorBoard writer
        if self.tb_writer is not None:
            self.tb_writer.close()

        self.stop_workers()
