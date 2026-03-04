"""
WebSocket服务（Streamlit集成）
"""

import streamlit as st
from typing import Optional, Dict, Any
from tetris_rl.env.tetris_env import TetrisEnv
from tetris_rl.ui.backends.html5.websocket_service import SimpleWebSocketService


class WebSocketManager:
    """WebSocket管理器"""

    def __init__(self, port: int = 8765):
        self.port = port
        self.service: Optional[SimpleWebSocketService] = None

    def start(self, game_env: Optional[TetrisEnv] = None) -> bool:
        """启动WebSocket服务"""
        try:
            if self.service and self.service.is_running():
                return True

            self.service = SimpleWebSocketService(port=self.port)
            self.service.start(game_env)
            return True
        except Exception as e:
            st.error(f"WebSocket服务启动失败: {e}")
            return False

    def stop(self) -> None:
        """停止WebSocket服务"""
        if self.service:
            self.service.stop()
            self.service = None

    def is_running(self) -> bool:
        """检查服务是否运行"""
        return self.service is not None and self.service.is_running()

    def get_server(self):
        """获取服务器实例"""
        return self.service.get_server() if self.service else None

    def get_websocket_url(self) -> str:
        """获取WebSocket URL"""
        return f"ws://localhost:{self.port}/ws/game"


def get_or_create_websocket_manager(port: int = 8765) -> WebSocketManager:
    """获取或创建WebSocket管理器（Streamlit会话状态）"""
    if "websocket_manager" not in st.session_state:
        st.session_state.websocket_manager = WebSocketManager(port)

    return st.session_state.websocket_manager


def init_websocket_for_demo() -> str:
    """为演示初始化WebSocket服务"""
    manager = get_or_create_websocket_manager()

    if not manager.is_running():
        # 创建演示环境
        from tetris_rl.env.tetris_env import TetrisEnv
        from tetris_rl.trainer.ppo_trainer import PPOConfig, RewardConfig

        cfg = PPOConfig(workers=1, reward=RewardConfig())
        env = TetrisEnv(seed=cfg.seed + 999, reward=cfg.reward, max_actions=cfg.max_actions)
        env.reset()

        manager.start(env)

    return manager.get_websocket_url()


def render_websocket_controls() -> None:
    """渲染WebSocket控制面板"""
    st.sidebar.subheader("🌐 WebSocket连接")

    manager = get_or_create_websocket_manager()

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if not manager.is_running():
            if st.button("启动连接", use_container_width=True):
                if manager.start():
                    st.success("WebSocket服务已启动")
                    st.rerun()
        else:
            if st.button("停止连接", use_container_width=True):
                manager.stop()
                st.info("WebSocket服务已停止")
                st.rerun()

    with col2:
        if manager.is_running():
            st.success("🟢 运行中")
        else:
            st.warning("🔴 已停止")

    # 连接信息
    if manager.is_running():
        st.sidebar.markdown("**连接信息**")
        st.sidebar.code(manager.get_websocket_url(), language="text")

        server = manager.get_server()
        if server and hasattr(server, 'clients'):
            client_count = len(server.clients)
            st.sidebar.metric("客户端连接数", client_count)