"""
Tetris RL 可视化模块
支持多种后端：streamlit (推荐)、pyqt6 (传统)、cli (命令行)
"""

import warnings
from typing import Optional


def launch_app(backend: str = "streamlit", **kwargs):
    """
    启动可视化应用

    Args:
        backend: 可视化后端，可选值: "streamlit", "pyqt6", "cli"
        **kwargs: 后端特定参数
    """
    if backend == "streamlit":
        try:
            import streamlit.web.cli as stcli
            import sys
            import os

            # 获取streamlit_app.py的路径
            app_path = os.path.join(os.path.dirname(__file__), "streamlit_app.py")

            # 设置streamlit命令行参数
            sys.argv = ["streamlit", "run", app_path, "--server.port", str(kwargs.get("port", 8501))]

            # 启动streamlit
            stcli.main()
        except ImportError:
            warnings.warn("Streamlit未安装，请使用: pip install streamlit")
            raise
        except Exception as e:
            print(f"Streamlit启动失败: {e}")
            raise

    elif backend == "pyqt6":
        warnings.warn(
            "PyQt6后端可能存在启动问题，建议使用streamlit后端",
            DeprecationWarning
        )
        try:
            from .legacy.main_window import MainWindow
            import sys
            from PyQt6.QtWidgets import QApplication

            app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            sys.exit(app.exec())
        except ImportError as e:
            warnings.warn(f"PyQt6后端导入失败: {e}")
            raise

    elif backend == "cli":
        from .cli_app import main
        main()
    else:
        raise ValueError(f"未知后端: {backend}")


def launch_streamlit(**kwargs):
    """启动Streamlit应用（快捷方式）"""
    return launch_app("streamlit", **kwargs)


def launch_pyqt6(**kwargs):
    """启动PyQt6应用（快捷方式）"""
    return launch_app("pyqt6", **kwargs)


# 保持现有导入（向后兼容）
try:
    from .legacy.main_window import MainWindow
    from .legacy.game_canvas import GameCanvas
    from .legacy.plots import LivePlots
    from .legacy.training_panel import TrainingPanel
    from .legacy.splash import SplashScreen
except ImportError:
    # 新安装可能没有legacy模块
    pass


# 导出核心模块
try:
    from .core import (
        RenderConfig,
        GameState,
        GameRenderer,
        ChartRenderer,
        UIController,
        VisualizationConfig,
        BackendRegistry,
        register_backend,
        BACKEND_HTML5,
        BACKEND_MATPLOTLIB,
        BACKEND_TEXT,
        BACKEND_PYQT6
    )

    __all__ = [
        "launch_app",
        "launch_streamlit",
        "launch_pyqt6",
        "RenderConfig",
        "GameState",
        "GameRenderer",
        "ChartRenderer",
        "UIController",
        "VisualizationConfig",
        "BackendRegistry",
        "register_backend",
        "BACKEND_HTML5",
        "BACKEND_MATPLOTLIB",
        "BACKEND_TEXT",
        "BACKEND_PYQT6",
        "MainWindow",
        "GameCanvas",
        "LivePlots",
        "TrainingPanel",
        "SplashScreen"
    ]
except ImportError:
    __all__ = ["launch_app", "launch_streamlit", "launch_pyqt6"]