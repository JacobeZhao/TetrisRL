"""
HTML5 Canvas 后端实现
"""

from __future__ import annotations
from tetris_rl.ui.core.visualizer import VisualizationBackend, RenderConfig
from tetris_rl.ui.core.factory import register_backend, BACKEND_HTML5


@register_backend(BACKEND_HTML5)
class HTML5Backend(VisualizationBackend):
    """HTML5 Canvas 后端"""

    def __init__(self, config: RenderConfig):
        super().__init__(config)
        # 延迟导入，避免循环依赖
        self._game_renderer = None
        self._chart_renderer = None
        self._ui_controller = None

    def create_game_renderer(self):
        """创建HTML5 Canvas游戏渲染器"""
        if self._game_renderer is None:
            from .canvas_renderer import HTML5CanvasRenderer
            self._game_renderer = HTML5CanvasRenderer(self.config)
        return self._game_renderer

    def create_chart_renderer(self):
        """创建HTML5图表渲染器"""
        if self._chart_renderer is None:
            from .chart_renderer import HTML5ChartRenderer
            self._chart_renderer = HTML5ChartRenderer(self.config)
        return self._chart_renderer

    def create_ui_controller(self):
        """创建HTML5 UI控制器"""
        if self._ui_controller is None:
            from .ui_controller import HTML5UIController
            self._ui_controller = HTML5UIController(self.config)
        return self._ui_controller