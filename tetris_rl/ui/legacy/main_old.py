from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMessageBox


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Try to import PyTorch (this is the main bottleneck)
    try:
        import torch
    except OSError as e:
        text = (
            "PyTorch 导入失败（Windows DLL 初始化失败）。\n\n"
            f"错误信息：{e}\n\n"
            "常见解决方法：\n"
            "1) 安装/修复 Microsoft Visual C++ Redistributable 2015-2022 (x64)\n"
            "2) 重新安装 torch（建议先安装 CPU 版本验证）：\n"
            "   pip uninstall -y torch\n"
            "   pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
            "3) 确认 Python 为 64-bit，并尽量使用 Python 3.11/3.12 的官方版本\n"
            "4) 如使用 GPU 版本，更新显卡驱动与 CUDA 运行时\n"
        )
        QMessageBox.critical(None, "PyTorch Import Error", text)
        return 1

    # Import and create splash screen
    from tetris_rl.ui.splash import SplashScreen

    splash = SplashScreen(app)
    splash.show()

    # Process events to ensure splash is visible
    app.processEvents()

    # Import MainWindow (also imports heavy components)
    splash.update_progress(1)
    from tetris_rl.ui.main_window import MainWindow

    splash.update_progress(2)

    # Connect splash progress to MainWindow
    def on_init_progress(progress: int, status: str) -> None:
        # Map internal progress to splash progress (20% to 100%)
        splash_progress = 20 + int(progress * 0.8)
        splash.set_progress(splash_progress)
        if status:
            splash.set_status(status)

    # Create MainWindow
    splash.update_progress(3)
    w = MainWindow()
    w.init_progress.connect(on_init_progress)

    # Wait a moment for window to be ready
    app.processEvents()

    # Close splash and show main window
    splash.update_progress(5)
    splash.close()
    w.show()

    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
