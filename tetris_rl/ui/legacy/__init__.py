"""
遗留UI模块，保持向后兼容
包含从tetris_rl.ui迁移过来的旧UI文件

注意: 这些文件已不再维护，建议使用新的模块化架构
"""

# 重新导出旧模块
try:
    from .main_window import MainWindow
    from .game_canvas import GameCanvas
    from .plots import LivePlots
    from .training_panel import TrainingPanel
    from .splash import SplashScreen

    __all__ = [
        "MainWindow",
        "GameCanvas",
        "LivePlots",
        "TrainingPanel",
        "SplashScreen"
    ]
except ImportError:
    # 如果某些模块导入失败，继续
    __all__ = []