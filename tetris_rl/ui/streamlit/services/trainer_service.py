"""
训练服务
基于现有_TrainerService的适配器
"""

import queue
import threading
import time
from typing import Any, Optional, Dict, List
from pathlib import Path


class TrainerService:
    """训练服务（适配现有_TrainerService）"""

    def __init__(self):
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._metrics_q: queue.Queue[Dict[str, Any]] = queue.Queue()
        self._latest_state: Optional[Dict[str, Any]] = None
        self._status: str = "Idle"
        self._cfg: Any = None
        self._trainer: Any = None

    def status(self) -> str:
        """获取当前状态"""
        with self._lock:
            return self._status

    def is_running(self) -> bool:
        """检查是否正在运行"""
        t = self._thread
        return t is not None and t.is_alive()

    def drain_metrics(self) -> List[Dict[str, Any]]:
        """获取所有累积的指标"""
        out: List[Dict[str, Any]] = []
        while True:
            try:
                out.append(self._metrics_q.get_nowait())
            except queue.Empty:
                break
        return out

    def latest_state_dict(self) -> Optional[Dict[str, Any]]:
        """获取最新的模型状态字典"""
        with self._lock:
            if self._latest_state is None:
                return None
            return dict(self._latest_state)

    def set_config(self, cfg: Any) -> None:
        """设置训练配置"""
        with self._lock:
            self._cfg = cfg

    def get_config(self) -> Any:
        """获取训练配置"""
        with self._lock:
            return self._cfg

    def start(self) -> None:
        """开始训练"""
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

                def on_update(payload: Dict[str, Any]) -> None:
                    with self._lock:
                        if trainer.model:
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
        """停止训练"""
        self._stop.set()

    def load_model(self, path: Path) -> None:
        """加载模型"""
        cfg = self.get_config()
        if cfg is None:
            return

        from tetris_rl.trainer.ppo_trainer import PPOTrainer

        trainer = self._trainer or PPOTrainer(cfg)
        trainer.cfg = cfg
        trainer.load_checkpoint(path)
        self._trainer = trainer

        with self._lock:
            if trainer.model:
                self._latest_state = {k: v.detach().cpu() for k, v in trainer.model.state_dict().items()}
            self._status = "Demo"

    def save_model(self, tag: str) -> Optional[Path]:
        """保存模型"""
        cfg = self.get_config()
        if cfg is None:
            return None

        from tetris_rl.trainer.ppo_trainer import PPOTrainer

        trainer = self._trainer or PPOTrainer(cfg)
        trainer.cfg = cfg
        self._trainer = trainer
        return trainer.save_checkpoint(tag=tag)

    def get_game_state(self) -> Optional[Dict[str, Any]]:
        """获取当前游戏状态"""
        if self._trainer is None or not hasattr(self._trainer, 'env'):
            return None

        try:
            env = self._trainer.env
            if env is None:
                return None

            return {
                "board": env.game.get_board_with_active(),
                "score": env.game.score,
                "lines_cleared": env.game.lines_cleared,
                "level": env.game.level,
                "next_piece": env.game.next_piece.id if env.game.next_piece else 0,
                "game_over": env.game.game_over
            }
        except Exception:
            return None

    def reset(self) -> None:
        """重置训练器"""
        with self._lock:
            self._stop.set()
            self._thread = None
            self._metrics_q = queue.Queue()
            self._latest_state = None
            self._status = "Idle"
            # 保持配置和训练器实例


def get_or_create_service() -> TrainerService:
    """获取或创建训练服务（Streamlit会话状态）"""
    import streamlit as st

    if "trainer_service" not in st.session_state:
        st.session_state.trainer_service = TrainerService()

    return st.session_state.trainer_service