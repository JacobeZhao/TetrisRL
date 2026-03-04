"""
可视化抽象层定义
定义游戏渲染器、图表渲染器和UI控制器的统一接口
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, Optional


@dataclass
class RenderConfig:
    """渲染配置基类"""
    cell_size: int = 30
    show_grid: bool = True
    show_ghost_piece: bool = True
    theme: str = "dark"


@dataclass
class GameState:
    """游戏状态数据容器"""
    board: list[list[int]]
    current_piece: Optional[tuple[int, int, int, int]] = None  # (piece_id, rotation, x, y)
    next_piece: Optional[int] = None
    score: int = 0
    lines_cleared: int = 0
    level: int = 1
    game_over: bool = False


class GameRenderer(Protocol):
    """游戏渲染器接口协议"""

    def render(self, state: GameState, config: RenderConfig) -> Any:
        """
        渲染游戏状态

        Args:
            state: 游戏状态数据
            config: 渲染配置

        Returns:
            渲染结果（图像、HTML、文本等）
        """
        ...

    def update_config(self, config: RenderConfig) -> None:
        """更新渲染配置"""
        ...


class ChartRenderer(Protocol):
    """图表渲染器接口协议"""

    def update_data(self, data: dict[str, list[tuple[int, float]]]) -> None:
        """
        更新图表数据

        Args:
            data: 图表数据字典，键为数据系列名称，值为（x, y）坐标列表
        """
        ...

    def render(self) -> Any:
        """
        渲染图表

        Returns:
            图表渲染结果
        """
        ...


class UIController(Protocol):
    """UI控制器接口协议"""

    def on_training_start(self, callback) -> None:
        """训练开始事件回调注册"""
        ...

    def on_training_stop(self, callback) -> None:
        """训练停止事件回调注册"""
        ...

    def on_training_pause(self, callback) -> None:
        """训练暂停事件回调注册"""
        ...

    def on_training_reset(self, callback) -> None:
        """训练重置事件回调注册"""
        ...

    def on_model_load(self, callback) -> None:
        """模型加载事件回调注册"""
        ...

    def on_model_save(self, callback) -> None:
        """模型保存事件回调注册"""
        ...


class VisualizationBackend(ABC):
    """可视化后端抽象基类"""

    def __init__(self, config: RenderConfig):
        self.config = config

    @abstractmethod
    def create_game_renderer(self) -> GameRenderer:
        """创建游戏渲染器"""
        pass

    @abstractmethod
    def create_chart_renderer(self) -> ChartRenderer:
        """创建图表渲染器"""
        pass

    @abstractmethod
    def create_ui_controller(self) -> UIController:
        """创建UI控制器"""
        pass