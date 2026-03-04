"""
Tetris RL 可视化核心模块
提供抽象层接口和工厂模式
"""

from .visualizer import (
    RenderConfig,
    GameState,
    GameRenderer,
    ChartRenderer,
    UIController,
    VisualizationBackend
)
from .config import VisualizationConfig
from .factory import (
    BackendRegistry,
    register_backend,
    BACKEND_HTML5,
    BACKEND_MATPLOTLIB,
    BACKEND_TEXT,
    BACKEND_PYQT6
)

__all__ = [
    "RenderConfig",
    "GameState",
    "GameRenderer",
    "ChartRenderer",
    "UIController",
    "VisualizationBackend",
    "VisualizationConfig",
    "BackendRegistry",
    "register_backend",
    "BACKEND_HTML5",
    "BACKEND_MATPLOTLIB",
    "BACKEND_TEXT",
    "BACKEND_PYQT6"
]