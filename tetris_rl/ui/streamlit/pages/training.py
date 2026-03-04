"""
训练页面
"""

import streamlit as st

st.set_page_config(page_title="训练 - Tetris RL", page_icon="🏋️")

st.title("🏋️ 训练")

# 页面描述
st.markdown("""
在此页面配置和监控强化学习训练过程。您可以调整训练参数、启动/停止训练，并实时查看训练曲线。
""")

# 初始化服务
from tetris_rl.ui.streamlit.services.trainer_service import get_or_create_service
from tetris_rl.ui.streamlit.components.control_panel import ControlPanel
from tetris_rl.ui.streamlit.components.charts import LiveCharts

# 获取服务
trainer_service = get_or_create_service()

# 创建两列布局
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("⚙️ 配置")

    # 后端选择
    from tetris_rl.ui.core.factory import BackendRegistry
    backends = BackendRegistry.list_backends()
    selected_backend = st.selectbox("渲染后端", backends, index=0 if backends else 0)

    # 创建后端
    from tetris_rl.ui.core.config import VisualizationConfig
    from tetris_rl.ui.core.factory import BackendRegistry

    if "viz_config" not in st.session_state:
        st.session_state.viz_config = VisualizationConfig()

    try:
        backend = BackendRegistry.create_backend(selected_backend, st.session_state.viz_config)
        st.session_state.backend = backend
    except Exception as e:
        st.error(f"后端创建失败: {e}")
        st.stop()

    # 控制面板
    controller = backend.create_ui_controller()
    control_panel = ControlPanel(controller)
    control_panel.render()

with col2:
    st.subheader("📊 训练监控")

    # 图表
    chart_renderer = backend.create_chart_renderer()
    charts = LiveCharts(chart_renderer)

    # 获取训练指标
    metrics = trainer_service.drain_metrics()
    if metrics:
        for metric in metrics:
            update_num = metric.get("update", 0)
            loss = metric.get("loss_policy", 0.0) + metric.get("loss_value", 0.0)
            score = metric.get("mean_episode_score", 0.0)

            charts.add_data_point("loss", update_num, loss)
            charts.add_data_point("score", update_num, score)

    # 渲染图表
    charts.render()

    # 训练状态
    st.subheader("📈 训练状态")
    status = trainer_service.status()
    st.info(f"**状态**: {status}")

    if trainer_service.is_running():
        st.progress(0.5, text="训练进行中...")
    else:
        st.progress(0.0, text="训练已停止")

    # 模型状态
    st.subheader("🤖 模型状态")
    state_dict = trainer_service.latest_state_dict()
    if state_dict:
        st.success("✅ 模型已加载")
        st.code(f"参数量: {len(state_dict)} 个张量")
    else:
        st.warning("⚠️ 模型未加载")

# 底部说明
st.divider()
st.markdown("""
### 使用说明

1. **配置训练参数**: 在左侧面板调整训练参数
2. **启动训练**: 点击"开始训练"按钮启动训练过程
3. **监控进度**: 在右侧查看实时训练曲线和状态
4. **保存模型**: 训练过程中或完成后可保存模型

### 注意事项

- 训练过程中请勿关闭浏览器标签页
- 模型会自动保存检查点
- 训练曲线数据仅保存在当前会话中
""")