"""
游戏棋盘组件
"""

import streamlit as st
from typing import Optional, Any
from tetris_rl.ui.core.visualizer import GameRenderer, GameState


class GameBoard:
    def __init__(self, renderer: GameRenderer):
        self.renderer = renderer
        self.game_state: Optional[GameState] = None

    def update_state(self, state: GameState):
        """更新游戏状态"""
        self.game_state = state

    def render(self):
        """渲染游戏棋盘"""
        st.subheader("🎮 游戏演示")

        if self.game_state:
            # 使用渲染器渲染游戏
            rendered = self.renderer.render(self.game_state, self.renderer.config)

            # 根据渲染类型显示
            if isinstance(rendered, str) and rendered.startswith("<"):
                # HTML内容
                st.components.v1.html(rendered, height=600)
            elif isinstance(rendered, bytes):
                # 图像数据
                st.image(rendered)
            else:
                # 文本或其他格式
                st.write(rendered)

            # 游戏统计信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("得分", self.game_state.score)
            with col2:
                st.metric("消除行数", self.game_state.lines_cleared)
            with col3:
                st.metric("等级", self.game_state.level)
        else:
            st.info("等待游戏状态更新...")

    def render_with_controls(self, on_action_callback=None):
        """渲染游戏棋盘和控制按钮"""
        self.render()

        # 添加控制按钮
        if on_action_callback:
            st.subheader("控制")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("左移", use_container_width=True):
                    on_action_callback("left")

            with col2:
                if st.button("右移", use_container_width=True):
                    on_action_callback("right")

            with col3:
                if st.button("旋转", use_container_width=True):
                    on_action_callback("rotate")

            with col4:
                if st.button("下落", use_container_width=True):
                    on_action_callback("drop")

    @staticmethod
    def create_demo_state() -> GameState:
        """创建演示游戏状态"""
        import random
        from tetris_rl.ui.core.visualizer import GameState

        # 创建10x20的棋盘
        board = [[0 for _ in range(10)] for _ in range(20)]

        # 添加一些方块
        for _ in range(40):
            x = random.randint(0, 9)
            y = random.randint(0, 19)
            piece_id = random.randint(1, 7)
            board[y][x] = piece_id

        return GameState(
            board=board,
            current_piece=(random.randint(1, 7), 0, random.randint(0, 6), 0),
            next_piece=random.randint(1, 7),
            score=random.randint(100, 10000),
            lines_cleared=random.randint(0, 100),
            level=random.randint(1, 10),
            game_over=False
        )