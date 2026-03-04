"""
演示页面
"""

import streamlit as st

st.set_page_config(page_title="演示 - Tetris RL", page_icon="🎮")

st.title("🎮 演示")

# 页面描述
st.markdown("""
在此页面观看训练好的模型玩俄罗斯方块，或手动控制游戏。
""")

# 初始化服务
from tetris_rl.ui.streamlit.services.websocket_service import init_websocket_for_demo, render_websocket_controls
from tetris_rl.ui.streamlit.components.game_board import GameBoard

# WebSocket控制
render_websocket_controls()

# 创建两列布局
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎮 游戏演示")

    # 后端选择
    from tetris_rl.ui.core.factory import BackendRegistry
    backends = BackendRegistry.list_backends()
    selected_backend = st.selectbox("渲染后端", backends, index=0 if backends else 0, key="demo_backend")

    # 创建后端和游戏棋盘
    from tetris_rl.ui.core.config import VisualizationConfig
    from tetris_rl.ui.core.factory import BackendRegistry

    if "viz_config" not in st.session_state:
        st.session_state.viz_config = VisualizationConfig()

    try:
        backend = BackendRegistry.create_backend(selected_backend, st.session_state.viz_config)
        game_renderer = backend.create_game_renderer()
        game_board = GameBoard(game_renderer)

        # 获取演示游戏状态
        from tetris_rl.ui.streamlit.services.trainer_service import get_or_create_service
        trainer_service = get_or_create_service()

        game_state_data = trainer_service.get_game_state()
        if game_state_data:
            from tetris_rl.ui.core.visualizer import GameState
            game_state = GameState(
                board=game_state_data["board"],
                score=game_state_data["score"],
                lines_cleared=game_state_data["lines_cleared"],
                level=game_state_data["level"],
                game_over=game_state_data["game_over"]
            )
            game_board.update_state(game_state)
        else:
            # 使用演示状态
            game_board.update_state(GameBoard.create_demo_state())

        # 渲染游戏棋盘
        game_board.render()

    except Exception as e:
        st.error(f"游戏渲染失败: {e}")
        st.stop()

with col2:
    st.subheader("🎯 控制")

    # 游戏控制
    st.markdown("#### 手动控制")
    control_col1, control_col2, control_col3, control_col4 = st.columns(4)

    with control_col1:
        if st.button("← 左移", use_container_width=True):
            st.session_state.last_action = "left"

    with control_col2:
        if st.button("→ 右移", use_container_width=True):
            st.session_state.last_action = "right"

    with control_col3:
        if st.button("↻ 旋转", use_container_width=True):
            st.session_state.last_action = "rotate"

    with control_col4:
        if st.button("↓ 下落", use_container_width=True):
            st.session_state.last_action = "drop"

    # AI控制
    st.divider()
    st.markdown("#### AI控制")

    ai_mode = st.selectbox(
        "AI模式",
        ["PPO智能体", "随机动作", "规则基础", "人工演示"],
        index=0
    )

    ai_speed = st.slider("AI速度", 0.1, 5.0, 1.0, 0.1)

    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("启动AI", use_container_width=True, type="primary"):
            st.session_state.ai_running = True
            st.success("AI已启动")

    with col_stop:
        if st.button("停止AI", use_container_width=True):
            st.session_state.ai_running = False
            st.info("AI已停止")

    # 游戏设置
    st.divider()
    st.markdown("#### 游戏设置")

    show_grid = st.checkbox("显示网格", True, key="demo_show_grid")
    show_ghost = st.checkbox("显示幽灵方块", True, key="demo_show_ghost")
    cell_size = st.slider("方块大小", 10, 50, 30, key="demo_cell_size")

    # 更新配置
    if (show_grid != st.session_state.viz_config.show_grid or
        show_ghost != st.session_state.viz_config.show_ghost_piece or
        cell_size != st.session_state.viz_config.cell_size):

        st.session_state.viz_config.show_grid = show_grid
        st.session_state.viz_config.show_ghost_piece = show_ghost
        st.session_state.viz_config.cell_size = cell_size

        # 标记需要重新创建后端
        if "backend" in st.session_state:
            del st.session_state.backend

# 实时更新
st.divider()
st.subheader("🔄 实时更新")

auto_refresh = st.checkbox("自动刷新", True)
refresh_interval = st.slider("刷新间隔(秒)", 0.1, 5.0, 1.0, 0.1)

if auto_refresh:
    import time
    time.sleep(refresh_interval)
    st.rerun()

# 游戏统计
st.divider()
st.subheader("📊 游戏统计")

if 'game_state' in locals():
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

    with col_stat1:
        st.metric("得分", game_state.score)

    with col_stat2:
        st.metric("消除行数", game_state.lines_cleared)

    with col_stat3:
        st.metric("等级", game_state.level)

    with col_stat4:
        status = "进行中" if not game_state.game_over else "已结束"
        st.metric("状态", status)

# 底部说明
st.divider()
st.markdown("""
### 使用说明

1. **手动控制**: 使用方向按钮手动控制方块
2. **AI控制**: 选择AI模式并启动AI自动游戏
3. **游戏设置**: 调整视觉效果和游戏参数
4. **实时更新**: 启用自动刷新观看实时游戏状态

### 提示

- 手动控制和AI控制可以同时使用
- 游戏设置会立即生效
- 点击"停止AI"可以随时中断AI控制
""")