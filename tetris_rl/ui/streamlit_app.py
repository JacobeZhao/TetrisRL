"""
Tetris RL Streamlit 主应用
基于模块化可视化架构的多页面应用
"""

from __future__ import annotations

import streamlit as st

# 页面配置
st.set_page_config(
    page_title="Tetris RL - PPO Training",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/yourusername/tetris-rl",
        "Report a bug": "https://github.com/yourusername/tetris-rl/issues",
        "About": """
        # Tetris RL 训练系统

        基于PPO算法的俄罗斯方块强化学习训练系统。

        版本: 2.0.0 (新架构)
        作者: AI Lab
        """
    }
)

# 应用标题
st.title("🧊 Tetris RL - PPO Training System")
st.markdown("""
### 基于模块化可视化架构的强化学习训练平台

欢迎使用新一代Tetris RL训练系统！本系统提供完整的强化学习训练、演示、评估和管理功能。
""")

# 功能概览
st.subheader("🚀 主要功能")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    **🏋️ 训练**
    - 配置训练参数
    - 实时监控训练曲线
    - 自动保存检查点
    """)

with col2:
    st.markdown("""
    **🎮 演示**
    - 观看AI玩俄罗斯方块
    - 手动控制游戏
    - 实时WebSocket连接
    """)

with col3:
    st.markdown("""
    **📈 评估**
    - 分析训练历史
    - 比较不同模型
    - 生成评估报告
    """)

with col4:
    st.markdown("""
    **⚙️ 设置**
    - 系统配置
    - 可视化选项
    - 实验参数管理
    """)

# 快速开始
st.subheader("⚡ 快速开始")

quick_col1, quick_col2, quick_col3 = st.columns(3)

with quick_col1:
    if st.button("开始训练", type="primary", use_container_width=True):
        st.switch_page("pages/training.py")

with quick_col2:
    if st.button("观看演示", use_container_width=True):
        st.switch_page("pages/demo.py")

with quick_col3:
    if st.button("系统设置", use_container_width=True):
        st.switch_page("pages/settings.py")

# 系统状态
st.subheader("📊 系统状态")

status_col1, status_col2, status_col3, status_col4 = st.columns(4)

with status_col1:
    # 初始化配置
    from tetris_rl.ui.core.config import VisualizationConfig
    if "viz_config" not in st.session_state:
        st.session_state.viz_config = VisualizationConfig()
    st.metric("配置状态", "🟢 正常")

with status_col2:
    # 检查后端
    from tetris_rl.ui.core.factory import BackendRegistry
    backends = BackendRegistry.list_backends()
    st.metric("可用后端", len(backends))

with status_col3:
    # 检查模型目录
    import os
    model_dir = "runs/tetris_ppo"
    model_count = len([f for f in os.listdir(model_dir) if f.endswith(('.pt', '.pth'))]) if os.path.exists(model_dir) else 0
    st.metric("已保存模型", model_count)

with status_col4:
    # 检查服务状态
    try:
        from tetris_rl.ui.streamlit.services.trainer_service import get_or_create_service
        service = get_or_create_service()
        status = service.status()
        st.metric("训练服务", status)
    except:
        st.metric("训练服务", "未初始化")

# 侧边栏导航
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/tetris.png", width=80)
    st.title("导航")

    # 页面选择
    page = st.selectbox(
        "选择页面",
        [
            "🏠 主页",
            "🏋️ 训练",
            "🎮 演示",
            "📈 评估",
            "⚙️ 设置"
        ],
        index=0
    )

    # 页面跳转
    if page != "🏠 主页":
        if "🏋️ 训练" in page:
            st.switch_page("pages/training.py")
        elif "🎮 演示" in page:
            st.switch_page("pages/demo.py")
        elif "📈 评估" in page:
            st.switch_page("pages/evaluation.py")
        elif "⚙️ 设置" in page:
            st.switch_page("pages/settings.py")

    # 侧边栏设置
    st.divider()
    st.subheader("⚙️ 快速设置")

    # 后端选择
    from tetris_rl.ui.core.factory import BackendRegistry
    backends = BackendRegistry.list_backends()
    if backends:
        selected_backend = st.selectbox("渲染后端", backends, index=0)
        st.session_state.selected_backend = selected_backend

    # 主题切换
    theme = st.selectbox("主题", ["dark", "light", "blue"], index=0)
    if theme != st.session_state.viz_config.theme:
        st.session_state.viz_config.theme = theme
        st.rerun()

    # 侧边栏信息
    st.divider()
    st.markdown("**系统信息**")
    import sys
    st.caption(f"Python: {sys.version.split()[0]}")
    st.caption(f"Streamlit: {st.__version__}")

# 技术架构
st.divider()
st.subheader("🏗️ 技术架构")

st.markdown("""
新一代Tetris RL训练系统采用模块化架构设计：

### 核心特性

1. **模块化可视化层**
   - 抽象渲染接口
   - 多后端支持 (HTML5 Canvas, Matplotlib, PyQt6)
   - 统一配置系统

2. **实时通信**
   - WebSocket双向通信
   - 实时游戏状态推送
   - 低延迟交互

3. **可扩展架构**
   - 工厂模式后端管理
   - 插件化组件系统
   - 易于添加新功能

### 后端支持

- **HTML5 Canvas**: 高性能Web渲染，支持动画和交互
- **Matplotlib**: 传统图表渲染，兼容性好
- **PyQt6**: 传统桌面GUI（兼容模式）
- **Text**: 命令行/简单文本输出

### 部署选项

- **本地运行**: Streamlit本地服务器
- **Web部署**: 云平台部署
- **Docker容器**: 标准化部署
""")

# 底部信息
st.divider()
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>Tetris RL Training System v2.0.0 | 基于模块化可视化架构</p>
    <p>© 2023 AI Lab | 技术支持: yourusername@example.com</p>
</div>
""", unsafe_allow_html=True)

# 初始化检查
def initialize_system():
    """初始化系统"""
    import sys
    import os

    # 添加项目路径
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # 确保目录存在
    os.makedirs("runs/tetris_ppo", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

# 自动初始化
if "system_initialized" not in st.session_state:
    initialize_system()
    st.session_state.system_initialized = True