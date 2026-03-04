from __future__ import annotations

import threading
import traceback
from dataclasses import replace
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from tetris_rl.env.tetris_env import RewardConfig, TetrisEnv
from tetris_rl.model.ppo_model import ActorCritic
from tetris_rl.trainer.ppo_trainer import PPOConfig, PPOTrainer
from tetris_rl.ui.game_canvas import GameCanvas, NextPieceWidget
from tetris_rl.ui.plots import LivePlots
from tetris_rl.ui.training_panel import TrainingPanel


class TrainerController(QWidget):
    metrics = pyqtSignal(dict)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    model_updated = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._trainer: PPOTrainer | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._latest_state: dict[str, Any] | None = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def latest_state_dict(self) -> dict[str, Any] | None:
        with self._lock:
            if self._latest_state is None:
                return None
            return {k: v.clone() for k, v in self._latest_state.items()}

    def ensure_trainer(self, cfg: PPOConfig) -> PPOTrainer:
        if self._trainer is None:
            self._trainer = PPOTrainer(cfg)
        return self._trainer

    def start_training(self, cfg: PPOConfig) -> None:
        if self.is_running():
            return
        self._stop.clear()

        trainer = self.ensure_trainer(cfg)
        self.status.emit("Training")

        def run() -> None:
            try:
                trainer.cfg = cfg
                trainer.start_workers()

                def stop_flag() -> bool:
                    return self._stop.is_set()

                def on_update(payload: dict[str, Any]) -> None:
                    import torch
                    with self._lock:
                        self._latest_state = {k: v.detach().cpu() for k, v in trainer.model.state_dict().items()}
                    self.metrics.emit(payload)
                    self.model_updated.emit()

                trainer.train(stop_flag=stop_flag, on_update=on_update)
                self.status.emit("Idle")
            except Exception:
                self.error.emit(traceback.format_exc())
                self.status.emit("Idle")

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop_training(self) -> None:
        self._stop.set()

    def load_model(self, cfg: PPOConfig, path: Path) -> None:
        trainer = self.ensure_trainer(cfg)
        trainer.load_checkpoint(path)
        import torch
        with self._lock:
            self._latest_state = {k: v.detach().cpu() for k, v in trainer.model.state_dict().items()}
        self.model_updated.emit()

    def save_model(self, cfg: PPOConfig, tag: str) -> Optional[Path]:
        trainer = self.ensure_trainer(cfg)
        return trainer.save_checkpoint(tag=tag)


class MainWindow(QMainWindow):
    init_progress = pyqtSignal(int, str)  # progress (0-100), status text

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Tetris RL (PPO + Ray)")
        self.setMinimumSize(1200, 720)

        self._cfg = PPOConfig(out_dir="runs/tetris_ppo", reward=RewardConfig())

        # Loading state
        self._loading = True
        self._initialized = False

        # Initialize UI components immediately (fast)
        self.controller = TrainerController()
        self.canvas = GameCanvas(cell_px=26)
        self.next_piece = NextPieceWidget(cell_px=18)

        self.lbl_score = QLabel("Loading...")
        self.lbl_episode = QLabel("0")
        self.lbl_step = QLabel("0")

        for l in (self.lbl_score, self.lbl_episode, self.lbl_step):
            l.setStyleSheet("color: #cfd2ff; font-size: 16px;")

        self.panel = TrainingPanel()
        self.plots = LivePlots(max_points=500)
        self.plots.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Demo components - will be initialized later
        self._demo_env: TetrisEnv | None = None
        self._demo_model: Any | None = None
        self._demo_obs: np.ndarray | None = None
        self._demo_info: dict[str, Any] | None = None
        self._demo_steps = 0

        # Build UI
        self._build()
        self._wire()

        # Show empty board during loading
        self._show_loading_state()

        # Delay heavy initialization
        self._init_timer = QTimer(self)
        self._init_timer.setSingleShot(True)
        self._init_timer.timeout.connect(self._init_later)
        self._init_timer.start(50)  # Small delay to let UI show

    def _show_loading_state(self) -> None:
        """Show a loading state on the canvas."""
        import numpy as np
        empty_grid = np.zeros((20, 10), dtype=int)
        self.canvas.set_grid(empty_grid)
        self.next_piece.set_piece(None)

    def _init_later(self) -> None:
        """Initialize heavy components after UI is shown."""
        if self._initialized:
            return

        self.init_progress.emit(20, "Loading PyTorch...")
        try:
            # Import torch here to avoid blocking UI initialization
            import torch
            self._torch = torch
        except OSError as e:
            self._show_loading_error(f"PyTorch import failed: {e}")
            return

        self.init_progress.emit(40, "Initializing model...")
        try:
            self._demo_env = TetrisEnv(seed=self._cfg.seed + 999, reward=self._cfg.reward, max_actions=self._cfg.max_actions)
            obs_dim = int(self._demo_env.observation_space.shape[0])
            act_dim = int(self._demo_env.action_space.n)
            self._demo_model = ActorCritic(obs_dim, act_dim).to(torch.device("cpu"))
            self._demo_model.eval()
        except Exception as e:
            self._show_loading_error(f"Model initialization failed: {e}")
            return

        self.init_progress.emit(60, "Preparing demo environment...")
        try:
            self._demo_obs, info = self._demo_env.reset()
            self._demo_info = info
            self._demo_steps = 0
        except Exception as e:
            self._show_loading_error(f"Environment reset failed: {e}")
            return

        self.init_progress.emit(80, "Starting demo...")
        try:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._demo_tick)
            self._timer.start(self.panel.speed.value())
            self._refresh_view(action_text="-")
        except Exception as e:
            self._show_loading_error(f"Timer setup failed: {e}")
            return

        self.init_progress.emit(100, "Ready!")
        self._initialized = True
        self._loading = False
        self.lbl_score.setText("0")

    def _show_loading_error(self, message: str) -> None:
        """Show loading error and disable interactive features."""
        self.lbl_score.setText("Error")
        QMessageBox.critical(self, "Initialization Error", message)

    def _build(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        outer = QHBoxLayout(root)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(10)

        left.addWidget(self.canvas, stretch=1)
        left.addWidget(QLabel("Next"), stretch=0)
        left.addWidget(self.next_piece, stretch=0)

        stat_row = QHBoxLayout()
        stat_row.addWidget(QLabel("Score:"))
        stat_row.addWidget(self.lbl_score)
        stat_row.addSpacing(16)
        stat_row.addWidget(QLabel("Episode:"))
        stat_row.addWidget(self.lbl_episode)
        stat_row.addSpacing(16)
        stat_row.addWidget(QLabel("Step:"))
        stat_row.addWidget(self.lbl_step)
        stat_row.addStretch(1)
        left.addLayout(stat_row)

        right = QVBoxLayout()
        right.setSpacing(10)
        right.addWidget(self.panel, stretch=0)
        right.addWidget(self.plots, stretch=1)

        outer.addLayout(left, stretch=0)
        outer.addLayout(right, stretch=1)

        root.setStyleSheet(
            """
            QMainWindow, QWidget { background: #0f1016; color: #e7e7ff; }
            QGroupBox { border: 1px solid #2b2d3a; border-radius: 8px; margin-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; color: #cfd2ff; }
            QPushButton { background: #2a2d3b; border: 1px solid #3a3d50; padding: 8px 10px; border-radius: 8px; }
            QPushButton:hover { background: #34384a; }
            QPushButton:pressed { background: #232635; }
            QSlider::groove:horizontal { height: 6px; background: #2a2d3b; border-radius: 3px; }
            QSlider::handle:horizontal { width: 14px; background: #cfd2ff; margin: -6px 0; border-radius: 7px; }
            """
        )

    def _wire(self) -> None:
        self.panel.start_training.connect(self._on_start_training)
        self.panel.stop_training.connect(self._on_stop_training)
        self.panel.load_model.connect(self._on_load_model)
        self.panel.save_model.connect(self._on_save_model)
        self.panel.speed_changed.connect(self._on_speed_changed)
        self.panel.workers_changed.connect(self._on_workers_changed)

        self.controller.metrics.connect(self._on_metrics)
        self.controller.status.connect(self.panel.set_status)
        self.controller.error.connect(self._on_error)
        self.controller.model_updated.connect(self._on_model_updated)

    def _current_cfg(self) -> PPOConfig:
        return replace(self._cfg, workers=int(self.panel.workers.value()))

    def _on_start_training(self) -> None:
        self.plots.reset()
        self._cfg = self._current_cfg()
        self.controller.start_training(self._cfg)

    def _on_stop_training(self) -> None:
        self.controller.stop_training()

    def _on_load_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Model", str(Path.cwd()), "PyTorch (*.pt)")
        if not path:
            return
        self._cfg = self._current_cfg()
        self.controller.load_model(self._cfg, Path(path))
        self.panel.set_status("Demo")

    def _on_save_model(self) -> None:
        self._cfg = self._current_cfg()
        tag = "manual_save"
        out = self.controller.save_model(self._cfg, tag=tag)
        if out is not None:
            QMessageBox.information(self, "Saved", f"Saved checkpoint:\n{out}")

    def _on_speed_changed(self, v: int) -> None:
        self._timer.setInterval(int(v))

    def _on_workers_changed(self, _v: int) -> None:
        self._cfg = self._current_cfg()

    def _on_error(self, text: str) -> None:
        QMessageBox.critical(self, "Error", text)

    def _on_metrics(self, payload: dict) -> None:
        upd = int(payload.get("update", 0))
        loss = float(payload.get("loss_policy", 0.0)) + float(payload.get("loss_value", 0.0))
        score = float(payload.get("mean_episode_score", 0.0))
        self.plots.add(upd, loss, score)
        self.panel.set_status(f"Training (upd {upd})")

    def _on_model_updated(self) -> None:
        state = self.controller.latest_state_dict()
        if state is None:
            return
        self._demo_model.load_state_dict(state)
        self._demo_model.eval()

    def _demo_tick(self) -> None:
        if self._loading or self._demo_env is None or self._demo_model is None:
            return

        mask = self._demo_info["action_mask"]
        placements = self._demo_env.game.legal_final_placements()
        action, _logp, _v = self._demo_model.act(self._demo_obs, mask, deterministic=True)
        chosen = "-"
        if len(placements) > 0:
            idx = int(action)
            if idx >= len(placements):
                idx = 0
            rot, x, y = placements[idx]
            chosen = f"place rot={rot} x={x} y={y}"
            action = idx

        obs, _r, terminated, _truncated, info = self._demo_env.step(int(action))
        self._demo_obs = obs
        self._demo_info = info
        self._demo_steps += 1
        if terminated:
            self._demo_obs, self._demo_info = self._demo_env.reset()
            self._demo_steps = 0
        self._refresh_view(action_text=chosen)

    def _refresh_view(self, action_text: str) -> None:
        if self._demo_env is None:
            return
        grid = self._demo_env.game.get_board_with_active()
        self.canvas.set_grid(grid)
        self.next_piece.set_piece(self._demo_env.game.next_piece)

        self.lbl_score.setText(str(int(self._demo_env.game.score)))
        self.lbl_episode.setText(str(int(self._demo_env.game.episode)))
        self.lbl_step.setText(str(int(self._demo_steps)))
        self.panel.set_action(action_text)
