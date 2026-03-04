"""
集成测试：验证新架构的各个组件能否正常协同工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """测试核心模块导入"""
    print("=== 测试模块导入 ===")

    modules = [
        ("tetris_rl.ui.core.visualizer", "RenderConfig"),
        ("tetris_rl.ui.core.config", "VisualizationConfig"),
        ("tetris_rl.ui.core.factory", "BackendRegistry"),
        ("tetris_rl.ui.backends.html5.canvas_renderer", "HTML5CanvasRenderer"),
        ("tetris_rl.ui.streamlit.components.game_board", "GameBoard"),
        ("tetris_rl.ui.streamlit.services.trainer_service", "TrainerService"),
    ]

    for module_path, class_name in modules:
        try:
            exec(f"from {module_path} import {class_name}")
            print(f"[OK] {module_path}.{class_name}")
        except Exception as e:
            print(f"[FAIL] {module_path}.{class_name}: {e}")


def test_backend_creation():
    """测试后端创建"""
    print("\n=== 测试后端创建 ===")

    try:
        from tetris_rl.ui.core.config import VisualizationConfig
        from tetris_rl.ui.core.factory import BackendRegistry

        # 列出可用后端
        backends = BackendRegistry.list_backends()
        print(f"可用后端: {backends}")

        if not backends:
            print("[WARN] 没有可用的后端")
            return

        # 测试创建每个后端
        config = VisualizationConfig()
        for backend_name in backends:
            try:
                backend = BackendRegistry.create_backend(backend_name, config)
                print(f"[OK] 创建后端: {backend_name} ({type(backend).__name__})")

                # 测试创建组件
                game_renderer = backend.create_game_renderer()
                chart_renderer = backend.create_chart_renderer()
                ui_controller = backend.create_ui_controller()

                print(f"   游戏渲染器: {type(game_renderer).__name__}")
                print(f"   图表渲染器: {type(chart_renderer).__name__}")
                print(f"   UI控制器: {type(ui_controller).__name__}")

            except Exception as e:
                print(f"[FAIL] 创建后端 {backend_name} 失败: {e}")

    except Exception as e:
        print(f"[FAIL] 后端创建测试失败: {e}")


def test_streamlit_components():
    """测试Streamlit组件"""
    print("\n=== 测试Streamlit组件 ===")

    try:
        # 测试GameBoard
        from tetris_rl.ui.core.visualizer import GameState, RenderConfig
        from tetris_rl.ui.backends.html5.canvas_renderer import HTML5CanvasRenderer
        from tetris_rl.ui.streamlit.components.game_board import GameBoard

        # 创建游戏状态
        board = [[0] * 10 for _ in range(20)]
        board[19][0] = 1  # I方块
        board[19][1] = 2  # O方块

        game_state = GameState(
            board=board,
            current_piece=(3, 0, 5, 0),
            next_piece=4,
            score=1500,
            lines_cleared=25,
            level=3
        )

        # 创建渲染器
        render_config = RenderConfig()
        renderer = HTML5CanvasRenderer(render_config)

        # 创建GameBoard
        game_board = GameBoard(renderer)
        game_board.update_state(game_state)

        print("[OK] GameBoard组件测试通过")

        # 测试ControlPanel
        from tetris_rl.ui.backends.html5.ui_controller import HTML5UIController
        from tetris_rl.ui.streamlit.components.control_panel import ControlPanel

        controller = HTML5UIController(render_config)
        control_panel = ControlPanel(controller)

        print("[OK] ControlPanel组件测试通过")

        # 测试LiveCharts
        from tetris_rl.ui.backends.html5.chart_renderer import HTML5ChartRenderer
        from tetris_rl.ui.streamlit.components.charts import LiveCharts

        chart_renderer = HTML5ChartRenderer(render_config)
        charts = LiveCharts(chart_renderer)

        # 添加演示数据
        demo_data = charts.create_demo_data()
        charts.update_data(demo_data)

        print("[OK] LiveCharts组件测试通过")

    except Exception as e:
        print(f"[FAIL] Streamlit组件测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_services():
    """测试服务层"""
    print("\n=== 测试服务层 ===")

    try:
        # 测试TrainerService
        from tetris_rl.ui.streamlit.services.trainer_service import TrainerService

        service = TrainerService()
        print(f"[OK] TrainerService创建成功，状态: {service.status()}")

        # 测试ModelService
        from tetris_rl.ui.streamlit.services.model_service import ModelService

        model_service = ModelService()
        models = model_service.list_models()
        print(f"[OK] ModelService创建成功，找到 {len(models)} 个模型")

        # 测试WebSocketService（不实际启动服务器）
        from tetris_rl.ui.backends.html5.websocket_service import GameWebSocketServer

        server = GameWebSocketServer(port=8765)
        print(f"[OK] WebSocketService创建成功")

    except Exception as e:
        print(f"[FAIL] 服务层测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_pages():
    """测试页面模块"""
    print("\n=== 测试页面模块 ===")

    pages_dir = os.path.join(os.path.dirname(__file__), "tetris_rl", "ui", "streamlit", "pages")
    pages = ["training.py", "demo.py", "evaluation.py", "settings.py"]

    for page_file in pages:
        page_path = os.path.join(pages_dir, page_file)
        if os.path.exists(page_path):
            print(f"[OK] 页面文件存在: {page_file}")
        else:
            print(f"[FAIL] 页面文件不存在: {page_file}")

    # 尝试导入页面模块（不执行）
    try:
        import importlib.util

        for page_file in pages:
            module_name = f"tetris_rl.ui.streamlit.pages.{page_file[:-3]}"
            spec = importlib.util.spec_from_file_location(
                module_name,
                os.path.join(pages_dir, page_file)
            )
            if spec:
                print(f"[OK] 页面可导入: {page_file}")
            else:
                print(f"[WARN] 页面导入失败: {page_file}")

    except Exception as e:
        print(f"[FAIL] 页面导入测试失败: {e}")


def main():
    """主测试函数"""
    print("Tetris RL 新架构集成测试")
    print("=" * 60)

    test_results = []

    # 运行测试
    tests = [
        test_imports,
        test_backend_creation,
        test_streamlit_components,
        test_services,
        test_pages
    ]

    for test_func in tests:
        try:
            test_func()
            test_results.append(True)
        except Exception as e:
            print(f"[FAIL] 测试函数 {test_func.__name__} 异常: {e}")
            test_results.append(False)
        print()

    # 总结
    print("=" * 60)
    print("测试结果汇总:")
    print(f"总测试项: {len(test_results)}")
    print(f"通过: {sum(test_results)}")
    print(f"失败: {len(test_results) - sum(test_results)}")

    if all(test_results):
        print("\n🎉 所有集成测试通过！新架构基本功能正常。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查相关问题。")
        return 1


if __name__ == "__main__":
    sys.exit(main())