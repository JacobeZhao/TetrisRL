"""
Tetris RL 主入口点
支持多种可视化后端启动
"""

from __future__ import annotations

import sys
import argparse
from typing import Optional


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Tetris RL 训练系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                         # 启动Streamlit Web UI (默认)
  %(prog)s --backend streamlit     # 启动Streamlit Web UI
  %(prog)s --backend pyqt6         # 启动PyQt6桌面应用
  %(prog)s --port 8502             # 指定Streamlit端口
  %(prog)s --help                  # 显示帮助信息
        """
    )

    parser.add_argument(
        "--backend",
        choices=["streamlit", "pyqt6", "cli"],
        default="streamlit",
        help="选择可视化后端 (默认: streamlit)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Streamlit服务器端口 (默认: 8501)"
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="服务器主机地址 (默认: localhost)"
    )

    parser.add_argument(
        "--config",
        help="配置文件路径"
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="启动演示模式"
    )

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="不自动打开浏览器 (仅Streamlit)"
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="显示版本信息"
    )

    return parser.parse_args()


def show_version() -> None:
    """显示版本信息"""
    version_info = {
        "Tetris RL": "2.0.0 (新架构)",
        "Python": f"{sys.version.split()[0]}",
        "平台": sys.platform
    }

    try:
        import torch
        version_info["PyTorch"] = torch.__version__
    except ImportError:
        pass

    try:
        import streamlit
        version_info["Streamlit"] = streamlit.__version__
    except ImportError:
        pass

    print("=" * 50)
    print("Tetris RL 训练系统")
    print("=" * 50)
    for key, value in version_info.items():
        print(f"{key:15} {value}")
    print("=" * 50)


def main() -> int:
    """主函数"""
    args = parse_args()

    # 显示版本信息
    if args.version:
        show_version()
        return 0

    # 根据后端启动应用
    if args.backend == "streamlit":
        return launch_streamlit(args)
    elif args.backend == "pyqt6":
        return launch_pyqt6(args)
    elif args.backend == "cli":
        return launch_cli(args)
    else:
        print(f"错误: 未知后端: {args.backend}")
        return 1


def launch_streamlit(args: argparse.Namespace) -> int:
    """启动Streamlit应用"""
    try:
        import streamlit.web.cli as stcli
        import os

        print("=" * 50)
        print("启动 Tetris RL Streamlit 应用")
        print(f"后端: Streamlit Web UI")
        print(f"地址: http://{args.host}:{args.port}")
        print("=" * 50)

        # 获取streamlit_app.py的路径
        app_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(app_dir, "ui", "streamlit_app.py")

        if not os.path.exists(app_path):
            print(f"错误: 找不到应用文件: {app_path}")
            return 1

        # 设置streamlit命令行参数
        sys.argv = ["streamlit", "run", app_path]

        # 添加可选参数
        if args.host != "localhost":
            sys.argv.extend(["--server.address", args.host])
        if args.port != 8501:
            sys.argv.extend(["--server.port", str(args.port)])
        if args.no_browser:
            sys.argv.append("--server.headless=true")
        if args.demo:
            sys.argv.extend(["--", "--demo"])

        # 启动streamlit
        stcli.main()
        return 0

    except ImportError:
        print("错误: Streamlit未安装")
        print("请使用: pip install streamlit")
        return 1
    except Exception as e:
        print(f"Streamlit启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


def launch_pyqt6(args: argparse.Namespace) -> int:
    """启动PyQt6应用"""
    import warnings
    warnings.warn(
        "PyQt6后端可能存在启动问题，建议使用streamlit后端",
        DeprecationWarning
    )

    try:
        from PyQt6.QtWidgets import QApplication
        from tetris_rl.ui.legacy.main_window import MainWindow

        print("=" * 50)
        print("启动 Tetris RL PyQt6 应用")
        print(f"后端: PyQt6 桌面应用")
        print("=" * 50)

        app = QApplication(sys.argv)
        app.setStyle("Fusion")

        # 尝试导入PyTorch
        try:
            import torch
        except OSError as e:
            print(f"PyTorch导入失败: {e}")
            print("请安装正确的PyTorch版本")
            return 1

        # 创建主窗口
        window = MainWindow()
        window.show()

        return int(app.exec())

    except ImportError as e:
        print(f"PyQt6导入失败: {e}")
        print("请确保已安装PyQt6: pip install PyQt6")
        return 1
    except Exception as e:
        print(f"PyQt6启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


def launch_cli(args: argparse.Namespace) -> int:
    """启动命令行应用"""
    print("=" * 50)
    print("启动 Tetris RL 命令行应用")
    print("=" * 50)

    try:
        # 这里可以实现CLI版本
        # 暂时使用占位符
        print("命令行版本正在开发中...")
        print("请使用 --backend streamlit 启动Web版本")

        # 简单训练演示
        from tetris_rl.env.tetris_env import TetrisEnv
        from tetris_rl.trainer.ppo_trainer import PPOConfig, RewardConfig

        print("\n启动简单训练演示...")
        cfg = PPOConfig(workers=1, reward=RewardConfig())
        env = TetrisEnv(seed=cfg.seed, reward=cfg.reward)

        obs, info = env.reset()
        print(f"初始状态: 分数={env.game.score}, 行数={env.game.lines_cleared}")

        # 执行几个随机动作
        for i in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            print(f"步骤 {i+1}: 动作={action}, 奖励={reward:.2f}, 分数={env.game.score}")

            if terminated:
                print("游戏结束!")
                break

        return 0

    except Exception as e:
        print(f"CLI启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())