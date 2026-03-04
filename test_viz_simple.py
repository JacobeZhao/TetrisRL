"""
测试可视化架构（简单版，无Unicode）
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tetris_rl.ui.core.visualizer import GameState, RenderConfig
from tetris_rl.ui.core.config import VisualizationConfig
from tetris_rl.ui.core.factory import BackendRegistry


def test_core_components():
    """测试核心组件"""
    print("=== 测试核心组件 ===")

    # 1. 测试RenderConfig
    render_config = RenderConfig(
        cell_size=30,
        show_grid=True,
        show_ghost_piece=True,
        theme="dark"
    )
    print(f"RenderConfig: cell_size={render_config.cell_size}, theme={render_config.theme}")

    # 2. 测试GameState
    board = [[0] * 10 for _ in range(20)]
    board[19][0] = 1
    board[19][1] = 2
    board[18][5] = 3

    game_state = GameState(
        board=board,
        current_piece=(4, 0, 5, 0),
        next_piece=5,
        score=1500,
        lines_cleared=25,
        level=3,
        game_over=False
    )
    print(f"GameState: score={game_state.score}, level={game_state.level}")

    # 3. 测试VisualizationConfig
    viz_config = VisualizationConfig()
    print(f"VisualizationConfig: theme={viz_config.theme}, cell_size={viz_config.cell_size}")

    # 保存和加载配置
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name

    try:
        viz_config.to_yaml(temp_path)
        print(f"配置已保存到: {temp_path}")

        loaded_config = VisualizationConfig.from_yaml(temp_path)
        print(f"配置已加载: theme={loaded_config.theme}")
    finally:
        os.unlink(temp_path)

    print("[OK] 核心组件测试通过")
    return True


def test_backend_registry():
    """测试后端注册表"""
    print("\n=== 测试后端注册表 ===")

    # 列出可用的后端
    backends = BackendRegistry.list_backends()
    print(f"可用后端: {backends}")

    if not backends:
        print("[WARN] 没有注册的后端")
        return False

    # 测试创建后端
    viz_config = VisualizationConfig()
    all_ok = True
    for backend_name in backends:
        try:
            backend = BackendRegistry.create_backend(backend_name, viz_config)
            print(f"[OK] 成功创建后端: {backend_name}")
            print(f"  后端类型: {type(backend).__name__}")

            # 测试创建组件
            game_renderer = backend.create_game_renderer()
            chart_renderer = backend.create_chart_renderer()
            ui_controller = backend.create_ui_controller()

            print(f"  游戏渲染器: {type(game_renderer).__name__}")
            print(f"  图表渲染器: {type(chart_renderer).__name__}")
            print(f"  UI控制器: {type(ui_controller).__name__}")

        except Exception as e:
            print(f"[FAIL] 创建后端失败 {backend_name}: {e}")
            all_ok = False

    print("[OK] 后端注册表测试完成")
    return all_ok


def test_html5_renderer():
    """测试HTML5渲染器"""
    print("\n=== 测试HTML5渲染器 ===")

    try:
        from tetris_rl.ui.backends.html5.canvas_renderer import HTML5CanvasRenderer
        from tetris_rl.ui.backends.html5.chart_renderer import HTML5ChartRenderer
        from tetris_rl.ui.backends.html5.ui_controller import HTML5UIController

        # 创建渲染器
        render_config = RenderConfig()
        renderer = HTML5CanvasRenderer(render_config)

        # 创建游戏状态
        board = [[0] * 10 for _ in range(20)]
        for i in range(5):
            board[19][i] = (i % 7) + 1

        game_state = GameState(
            board=board,
            current_piece=(3, 0, 5, 0),
            next_piece=2,
            score=2500,
            lines_cleared=50,
            level=5
        )

        # 渲染游戏
        html_output = renderer.render(game_state, render_config)
        print(f"HTML输出长度: {len(html_output)} 字符")
        print(f"包含canvas标签: {'<canvas' in html_output}")

        # 测试图表渲染器
        chart_renderer = HTML5ChartRenderer(render_config)
        data = {
            "loss": [(i, i * 0.1) for i in range(10)],
            "score": [(i, i * 10) for i in range(10)]
        }
        chart_renderer.update_data(data)
        chart_html = chart_renderer.render()
        print(f"图表HTML长度: {len(chart_html)} 字符")

        # 测试UI控制器
        ui_controller = HTML5UIController(render_config)

        # 注册回调
        def on_training_start(config):
            print(f"训练开始回调: {config}")

        ui_controller.on_training_start(on_training_start)
        ui_controller.trigger_training_start({"workers": 4})

        print("[OK] HTML5渲染器测试通过")
        return True

    except ImportError as e:
        print(f"[FAIL] HTML5渲染器导入失败: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] HTML5渲染器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("Tetris RL 可视化架构测试")
    print("=" * 50)

    try:
        results = []

        results.append(test_core_components())
        results.append(test_backend_registry())
        results.append(test_html5_renderer())

        print("\n" + "=" * 50)
        if all(results):
            print("所有测试通过！")
            return 0
        else:
            print("部分测试失败")
            return 1

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())