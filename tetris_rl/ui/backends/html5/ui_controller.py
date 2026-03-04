"""
HTML5 UI控制器
处理Streamlit UI事件
"""

from __future__ import annotations
from typing import Callable, Any, Optional
from tetris_rl.ui.core.visualizer import UIController, RenderConfig


class HTML5UIController(UIController):
    """HTML5 UI控制器"""

    def __init__(self, config: RenderConfig):
        self.config = config
        self._callbacks: dict[str, list[Callable]] = {
            'training_start': [],
            'training_stop': [],
            'training_pause': [],
            'training_reset': [],
            'model_load': [],
            'model_save': []
        }

    def _trigger_event(self, event_name: str, *args, **kwargs) -> None:
        """触发事件"""
        for callback in self._callbacks.get(event_name, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"事件回调执行失败 {event_name}: {e}")

    def on_training_start(self, callback: Callable) -> None:
        """注册训练开始事件回调"""
        self._callbacks['training_start'].append(callback)

    def on_training_stop(self, callback: Callable) -> None:
        """注册训练停止事件回调"""
        self._callbacks['training_stop'].append(callback)

    def on_training_pause(self, callback: Callable) -> None:
        """注册训练暂停事件回调"""
        self._callbacks['training_pause'].append(callback)

    def on_training_reset(self, callback: Callable) -> None:
        """注册训练重置事件回调"""
        self._callbacks['training_reset'].append(callback)

    def on_model_load(self, callback: Callable) -> None:
        """注册模型加载事件回调"""
        self._callbacks['model_load'].append(callback)

    def on_model_save(self, callback: Callable) -> None:
        """注册模型保存事件回调"""
        self._callbacks['model_save'].append(callback)

    # 事件触发方法（供UI调用）
    def trigger_training_start(self, config: Any = None) -> None:
        """触发训练开始事件"""
        self._trigger_event('training_start', config)

    def trigger_training_stop(self) -> None:
        """触发训练停止事件"""
        self._trigger_event('training_stop')

    def trigger_training_pause(self) -> None:
        """触发训练暂停事件"""
        self._trigger_event('training_pause')

    def trigger_training_reset(self) -> None:
        """触发训练重置事件"""
        self._trigger_event('training_reset')

    def trigger_model_load(self, model_path: str) -> None:
        """触发模型加载事件"""
        self._trigger_event('model_load', model_path)

    def trigger_model_save(self, tag: str = "manual_save") -> Optional[str]:
        """触发模型保存事件"""
        results = []
        for callback in self._callbacks['model_save']:
            try:
                result = callback(tag)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"模型保存回调执行失败: {e}")
        return results[0] if results else None