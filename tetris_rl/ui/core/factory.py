"""
后端工厂模式
负责创建特定后端的可视化组件
"""

from __future__ import annotations
from typing import Type, Dict, Any
from .visualizer import VisualizationBackend, RenderConfig
from .config import VisualizationConfig


class BackendRegistry:
    """后端注册表"""

    _backends: Dict[str, Type[VisualizationBackend]] = {}

    @classmethod
    def register(cls, name: str, backend_class: Type[VisualizationBackend]) -> None:
        """注册后端"""
        cls._backends[name] = backend_class

    @classmethod
    def get_backend_class(cls, name: str) -> Type[VisualizationBackend]:
        """获取后端类"""
        if name not in cls._backends:
            raise ValueError(f"未知的后端: {name}")
        return cls._backends[name]

    @classmethod
    def list_backends(cls) -> list[str]:
        """列出所有已注册的后端"""
        return list(cls._backends.keys())

    @classmethod
    def create_backend(cls, name: str, config: VisualizationConfig) -> VisualizationBackend:
        """创建后端实例"""
        backend_class = cls.get_backend_class(name)
        # 将VisualizationConfig转换为RenderConfig
        render_config = RenderConfig(
            cell_size=config.cell_size,
            show_grid=config.show_grid,
            show_ghost_piece=config.show_ghost_piece,
            theme=config.theme
        )
        return backend_class(render_config)


def register_backend(name: str):
    """后端注册装饰器"""
    def decorator(cls: Type[VisualizationBackend]) -> Type[VisualizationBackend]:
        BackendRegistry.register(name, cls)
        return cls
    return decorator


# 预定义后端名称
BACKEND_HTML5 = "html5"
BACKEND_MATPLOTLIB = "matplotlib"
BACKEND_TEXT = "text"
BACKEND_PYQT6 = "pyqt6"

# 导入并注册可用的后端
try:
    from tetris_rl.ui.backends.html5.backend import HTML5Backend
    # HTML5Backend已经通过装饰器注册
except ImportError as e:
    print(f"HTML5后端导入失败: {e}")

# 注册其他后端（占位符）
# try:
#     from tetris_rl.ui.backends.matplotlib.backend import MatplotlibBackend
# except ImportError:
#     pass