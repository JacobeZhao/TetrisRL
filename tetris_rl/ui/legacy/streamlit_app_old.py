from __future__ import annotations

import queue
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Optional

import numpy as np


class _TrainerService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._metrics_q: queue.Queue[dict[str, Any]] = queue.Queue()
        self._latest_state: dict[str, Any] | None = None
        self._status: str = "Idle"
        self._cfg: Any | None = None
        self._trainer: Any | None = None

    def status(self) -> str:
        with self._lock:
            return self._status

    def is_running(self) -> bool:
        t = self._thread
        return t is not None and t.is_alive()

    def drain_metrics(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        while True:
            try:
                out.append(self._metrics_q.get_nowait())
            except queue.Empty:
                break
        return out

    def latest_state_dict(self) -> dict[str, Any] | None:
        with self._lock:
            if self._latest_state is None:
                return None
            return dict(self._latest_state)

    def set_cfg(self, cfg: Any) -> None:
        with self._lock:
            self._cfg = cfg

    def get_cfg(self) -> Any | None:
        with self._lock:
            return self._cfg

    def start(self) -> None:
        if self.is_running():
            return
        self._stop.clear()

        def run() -> None:
            with self._lock:
                self._status = "Starting"
                cfg = self._cfg
            try:
                import torch

                from tetris_rl.trainer.ppo_trainer import PPOTrainer

                trainer = self._trainer or PPOTrainer(cfg)
                trainer.cfg = cfg
                self._trainer = trainer
                trainer.start_workers()

                def stop_flag() -> bool:
                    return self._stop.is_set()

                def on_update(payload: dict[str, Any]) -> None:
                    with self._lock:
                        self._latest_state = {k: v.detach().cpu() for k, v in trainer.model.state_dict().items()}
                        self._status = f"Training (upd {int(payload.get('update', 0))})"
                    self._metrics_q.put(payload)

                trainer.train(stop_flag=stop_flag, on_update=on_update)
                with self._lock:
                    self._status = "Idle"
            except Exception as e:
                with self._lock:
                    self._status = f"Error: {e}"

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def load_model(self, path: Path) -> None:
        cfg = self.get_cfg()
        if cfg is None:
            return
        from tetris_rl.trainer.ppo_trainer import PPOTrainer

        trainer = self._trainer or PPOTrainer(cfg)
        trainer.cfg = cfg
        trainer.load_checkpoint(path)
        self._trainer = trainer
        with self._lock:
            self._latest_state = {k: v.detach().cpu() for k, v in trainer.model.state_dict().items()}
            self._status = "Demo"

    def save_model(self, tag: str) -> Optional[Path]:
        cfg = self.get_cfg()
        if cfg is None:
            return None
        from tetris_rl.trainer.ppo_trainer import PPOTrainer

        trainer = self._trainer or PPOTrainer(cfg)
        trainer.cfg = cfg
        self._trainer = trainer
        return trainer.save_checkpoint(tag=tag)


def _render_board_png(board: list[list[int]]) -> bytes:
    import io

    import matplotlib.pyplot as plt

    from tetris_rl.core.constants import PIECE_COLORS_RGB, PIECE_ID_TO_NAME

    h = len(board)
    w = len(board[0]) if h > 0 else 0
    img = np.zeros((h, w, 3), dtype=np.float32)
    bg = np.array([12, 12, 16], dtype=np.float32) / 255.0
    img[:] = bg
    for y in range(h):
        for x in range(w):
            v = int(board[y][x])
            if v == 0:
                continue
            name = PIECE_ID_TO_NAME.get(v, "T")
            rgb = np.array(PIECE_COLORS_RGB.get(name, (200, 200, 200)), dtype=np.float32) / 255.0
            img[y, x] = rgb

    fig, ax = plt.subplots(figsize=(3.4, 6.2), dpi=140)
    ax.imshow(img, interpolation="nearest")
    ax.set_xticks(np.arange(-0.5, w, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, h, 1), minor=True)
    ax.grid(which="minor", color="#2b2d3a", linewidth=0.8)
    ax.tick_params(which="both", bottom=False, left=False, labelbottom=False, labelleft=False)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(2)
        spine.set_edgecolor("#dcdce6")
    buf = io.BytesIO()
    fig.tight_layout(pad=0.2)
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Tetris RL (PPO + Ray)", layout="wide")

    if "svc" not in st.session_state:
        st.session_state.svc = _TrainerService()
    svc: _TrainerService = st.session_state.svc

    if "history" not in st.session_state:
        st.session_state.history = {"update": [], "loss": [], "score": []}

    if "demo" not in st.session_state:
        st.session_state.demo = {}

    st.title("Tetris RL (PPO + Ray + Streamlit)")

    left, right = st.columns([0.9, 1.1], gap="large")

    with st.sidebar:
        st.subheader("Controls")
        workers = st.number_input("Workers", min_value=1, max_value=64, value=4, step=1)
        speed_ms = st.slider("Speed (ms)", min_value=10, max_value=500, value=120, step=10)
        auto_refresh = st.toggle("Auto Refresh", value=True)

        btn_row = st.columns(2)
        with btn_row[0]:
            if st.button("Start Training", use_container_width=True, disabled=svc.is_running()):
                from tetris_rl.trainer.ppo_trainer import PPOConfig

                cfg = PPOConfig(workers=int(workers))
                svc.set_cfg(cfg)
                svc.start()
        with btn_row[1]:
            if st.button("Stop", use_container_width=True, disabled=not svc.is_running()):
                svc.stop()

        st.divider()
        st.subheader("Model")
        up = st.file_uploader("Load checkpoint (.pt)", type=["pt"])
        if up is not None:
            tmp = Path(st.session_state.get("_upload_path", "runs/_uploaded.pt"))
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(up.getvalue())
            svc.load_model(tmp)
            st.success(f"Loaded: {tmp}")

        if st.button("Save checkpoint", use_container_width=True):
            from tetris_rl.trainer.ppo_trainer import PPOConfig

            cfg = svc.get_cfg() or PPOConfig(workers=int(workers))
            svc.set_cfg(cfg)
            out = svc.save_model(tag="manual_save")
            if out is not None and out.exists():
                st.success(f"Saved: {out}")
                st.download_button("Download", data=out.read_bytes(), file_name=out.name, use_container_width=True)

        st.divider()
        st.subheader("Status")
        st.write(svc.status())

    new = svc.drain_metrics()
    if len(new) > 0:
        for p in new:
            upd = int(p.get("update", 0))
            loss = float(p.get("loss_policy", 0.0)) + float(p.get("loss_value", 0.0))
            score = float(p.get("mean_episode_score", 0.0))
            st.session_state.history["update"].append(upd)
            st.session_state.history["loss"].append(loss)
            st.session_state.history["score"].append(score)

    with right:
        st.subheader("Live Curves")
        if len(st.session_state.history["update"]) > 0:
            import pandas as pd

            df = pd.DataFrame(st.session_state.history)
            c1, c2 = st.columns(2)
            with c1:
                st.line_chart(df, x="update", y="loss", height=240)
            with c2:
                st.line_chart(df, x="update", y="score", height=240)
        else:
            st.info("Start Training 后会显示 loss / score 曲线。")

    with left:
        st.subheader("Demo")
        from tetris_rl.env.tetris_env import RewardConfig, TetrisEnv

        if "env" not in st.session_state.demo:
            from tetris_rl.trainer.ppo_trainer import PPOConfig

            cfg = svc.get_cfg() or PPOConfig(workers=int(workers), reward=RewardConfig())
            svc.set_cfg(cfg)
            env = TetrisEnv(seed=cfg.seed + 999, reward=cfg.reward, max_actions=cfg.max_actions)
            obs, info = env.reset()
            st.session_state.demo["env"] = env
            st.session_state.demo["obs"] = obs
            st.session_state.demo["info"] = info
            st.session_state.demo["steps"] = 0

            import torch

            from tetris_rl.model.ppo_model import ActorCritic

            obs_dim = int(env.observation_space.shape[0])
            act_dim = int(env.action_space.n)
            model = ActorCritic(obs_dim, act_dim).to(torch.device("cpu"))
            model.eval()
            st.session_state.demo["model"] = model

        state = svc.latest_state_dict()
        if state is not None:
            try:
                st.session_state.demo["model"].load_state_dict(state)
                st.session_state.demo["model"].eval()
            except Exception:
                pass

        env: Any = st.session_state.demo["env"]
        obs: np.ndarray = st.session_state.demo["obs"]
        info: dict[str, Any] = st.session_state.demo["info"]

        import torch

        model = st.session_state.demo["model"]
        placements = env.game.legal_final_placements()
        action, _logp, _v = model.act(obs, info["action_mask"], deterministic=True)
        chosen = "-"
        if len(placements) > 0:
            idx = int(action)
            if idx >= len(placements):
                idx = 0
            rot, x, y = placements[idx]
            chosen = f"place rot={rot} x={x} y={y}"
            action = idx

        next_obs, _r, terminated, _truncated, next_info = env.step(int(action))
        st.session_state.demo["obs"] = next_obs
        st.session_state.demo["info"] = next_info
        st.session_state.demo["steps"] = int(st.session_state.demo["steps"]) + 1
        if terminated:
            obs, info = env.reset()
            st.session_state.demo["obs"] = obs
            st.session_state.demo["info"] = info
            st.session_state.demo["steps"] = 0

        grid = env.game.get_board_with_active()
        st.image(_render_board_png(grid), caption=f"Score={env.game.score}  Episode={env.game.episode}  Step={st.session_state.demo['steps']}  Action={chosen}")

    if auto_refresh:
        time.sleep(max(0.01, float(speed_ms) / 1000.0))
        st.rerun()


if __name__ == "__main__":
    main()

