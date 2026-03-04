from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import ray
import torch

from tetris_rl.env.tetris_env import RewardConfig, TetrisEnv
from tetris_rl.model.ppo_model import ActorCritic


@dataclass(frozen=True, slots=True)
class WorkerConfig:
    seed: int = 0
    max_actions: int = 64
    reward: RewardConfig | None = None


@ray.remote
class RolloutWorker:
    def __init__(self, obs_dim: int, act_dim: int, cfg: WorkerConfig, worker_id: int) -> None:
        self.cfg = cfg
        self.worker_id = int(worker_id)
        self.device = torch.device("cpu")
        self.env = TetrisEnv(seed=cfg.seed + 10_000 * self.worker_id, reward=cfg.reward, max_actions=cfg.max_actions)
        self.model = ActorCritic(obs_dim=obs_dim, act_dim=act_dim).to(self.device)
        self.model.eval()

        self._obs, info = self.env.reset(seed=cfg.seed + 10_000 * self.worker_id)
        self._mask = info["action_mask"].astype(np.float32, copy=False)

    def set_weights(self, state_dict: dict[str, Any]) -> None:
        self.model.load_state_dict(state_dict)
        self.model.eval()

    def rollout(self, steps: int) -> dict[str, Any]:
        T = int(steps)
        obs_buf = np.zeros((T, self._obs.shape[0]), dtype=np.float32)
        act_buf = np.zeros((T,), dtype=np.int64)
        logp_buf = np.zeros((T,), dtype=np.float32)
        val_buf = np.zeros((T,), dtype=np.float32)
        rew_buf = np.zeros((T,), dtype=np.float32)
        done_buf = np.zeros((T,), dtype=np.float32)
        mask_buf = np.zeros((T, self.env.action_space.n), dtype=np.float32)

        ep_scores: list[float] = []

        for t in range(T):
            obs_buf[t] = self._obs
            mask_buf[t] = self._mask
            a, logp, v = self.model.act(self._obs, self._mask, device=self.device, deterministic=False)
            act_buf[t] = a
            logp_buf[t] = logp
            val_buf[t] = v

            next_obs, r, terminated, _truncated, info = self.env.step(int(a))
            rew_buf[t] = float(r)
            done_buf[t] = 1.0 if terminated else 0.0

            self._obs = next_obs
            self._mask = info["action_mask"].astype(np.float32, copy=False)

            if terminated:
                ep_scores.append(float(info.get("score", 0.0)))
                self._obs, info = self.env.reset()
                self._mask = info["action_mask"].astype(np.float32, copy=False)

        last_done = bool(done_buf[-1] > 0.5)
        if last_done:
            last_value = 0.0
        else:
            with torch.no_grad():
                obs_t = torch.as_tensor(self._obs, dtype=torch.float32, device=self.device).unsqueeze(0)
                mask_t = torch.as_tensor(self._mask, dtype=torch.float32, device=self.device).unsqueeze(0)
                out = self.model.forward(obs_t)
                last_value = float(out.value.item())

        return {
            "obs": obs_buf,
            "actions": act_buf,
            "logprobs": logp_buf,
            "values": val_buf,
            "rewards": rew_buf,
            "dones": done_buf,
            "action_masks": mask_buf,
            "last_value": float(last_value),
            "episode_scores": np.array(ep_scores, dtype=np.float32),
        }
