"""
设置页面
"""

import streamlit as st
from pathlib import Path
import yaml

st.set_page_config(page_title="设置 - Tetris RL", page_icon="⚙️")

st.title("⚙️ 设置")

# 页面描述
st.markdown("""
在此页面配置系统设置、可视化选项和实验参数。
""")

# 创建标签页
tab1, tab2, tab3, tab4 = st.tabs(["系统设置", "可视化", "实验配置", "高级"])

with tab1:
    st.subheader("🔧 系统设置")

    # 基本设置
    st.markdown("#### 基本设置")

    log_level = st.selectbox(
        "日志级别",
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        index=1
    )

    auto_save = st.checkbox("自动保存检查点", True)
    save_interval = st.slider("保存间隔(分钟)", 5, 120, 30, 5, disabled=not auto_save)

    max_checkpoints = st.number_input("最大检查点数量", 1, 100, 10)

    # 资源设置
    st.markdown("#### 资源设置")

    use_gpu = st.checkbox("使用GPU加速", True)

    if use_gpu:
        gpu_id = st.selectbox("GPU设备", ["0", "1", "2", "3"], index=0)
        memory_limit = st.slider("GPU内存限制(GB)", 1, 32, 8, 1)
    else:
        st.info("使用CPU模式，性能可能受限")

    num_threads = st.slider("CPU线程数", 1, 32, 4)

    # 保存设置
    if st.button("保存系统设置", type="primary"):
        system_settings = {
            "log_level": log_level,
            "auto_save": auto_save,
            "save_interval": save_interval,
            "max_checkpoints": max_checkpoints,
            "use_gpu": use_gpu,
            "gpu_id": int(gpu_id) if use_gpu else None,
            "memory_limit": memory_limit if use_gpu else None,
            "num_threads": num_threads
        }

        st.session_state.system_settings = system_settings
        st.success("系统设置已保存")

with tab2:
    st.subheader("🎨 可视化设置")

    # 主题设置
    st.markdown("#### 主题设置")

    theme = st.selectbox(
        "主题",
        ["dark", "light", "blue", "green", "purple"],
        index=0
    )

    # 游戏渲染设置
    st.markdown("#### 游戏渲染设置")

    col1, col2 = st.columns(2)

    with col1:
        cell_size = st.slider("方块大小", 10, 50, 30)
        show_grid = st.checkbox("显示网格", True)
        show_ghost = st.checkbox("显示幽灵方块", True)

    with col2:
        animation_speed = st.slider("动画速度", 0.1, 3.0, 1.0, 0.1)
        render_quality = st.selectbox(
            "渲染质量",
            ["low", "medium", "high", "ultra"],
            index=2
        )
        fps_limit = st.slider("FPS限制", 30, 240, 60, 10)

    # 图表设置
    st.markdown("#### 图表设置")

    chart_theme = st.selectbox(
        "图表主题",
        ["plotly_dark", "plotly_white", "ggplot2", "seaborn"],
        index=0
    )

    chart_max_points = st.slider("最大数据点数", 100, 5000, 1000, 100)
    chart_update_interval = st.slider("图表更新间隔(秒)", 0.1, 10.0, 1.0, 0.1)

    # 保存可视化设置
    if st.button("保存可视化设置", type="primary"):
        viz_settings = {
            "theme": theme,
            "cell_size": cell_size,
            "show_grid": show_grid,
            "show_ghost": show_ghost,
            "animation_speed": animation_speed,
            "render_quality": render_quality,
            "fps_limit": fps_limit,
            "chart_theme": chart_theme,
            "chart_max_points": chart_max_points,
            "chart_update_interval": chart_update_interval
        }

        st.session_state.viz_settings = viz_settings
        st.success("可视化设置已保存")

with tab3:
    st.subheader("🧪 实验配置")

    # 实验参数
    st.markdown("#### 实验参数")

    experiment_name = st.text_input("实验名称", "tetris_ppo_experiment")
    experiment_description = st.text_area("实验描述", "PPO算法在俄罗斯方块环境中的训练实验")

    # 超参数配置
    st.markdown("#### 超参数配置")

    hyperparam_col1, hyperparam_col2 = st.columns(2)

    with hyperparam_col1:
        learning_rate = st.number_input("学习率", 1e-6, 1e-2, 3e-4, format="%.6f")
        gamma = st.slider("折扣因子 (gamma)", 0.9, 0.999, 0.99, 0.001)
        gae_lambda = st.slider("GAE lambda", 0.9, 1.0, 0.95, 0.01)

    with hyperparam_col2:
        clip_param = st.slider("裁剪参数", 0.1, 0.3, 0.2, 0.01)
        entropy_coef = st.slider("熵系数", 0.0, 0.1, 0.01, 0.001)
        value_loss_coef = st.slider("价值损失系数", 0.1, 2.0, 1.0, 0.1)

    # 训练配置
    st.markdown("#### 训练配置")

    total_updates = st.number_input("总更新次数", 1000, 1000000, 10000)
    batch_size = st.selectbox("批大小", [32, 64, 128, 256, 512], index=2)
    num_workers = st.slider("工作进程数", 1, 32, 4)

    # 保存实验配置
    if st.button("保存实验配置", type="primary"):
        experiment_config = {
            "experiment_name": experiment_name,
            "experiment_description": experiment_description,
            "hyperparameters": {
                "learning_rate": learning_rate,
                "gamma": gamma,
                "gae_lambda": gae_lambda,
                "clip_param": clip_param,
                "entropy_coef": entropy_coef,
                "value_loss_coef": value_loss_coef
            },
            "training": {
                "total_updates": total_updates,
                "batch_size": batch_size,
                "num_workers": num_workers
            }
        }

        st.session_state.experiment_config = experiment_config
        st.success("实验配置已保存")

with tab4:
    st.subheader("⚡ 高级设置")

    # 危险操作警告
    st.warning("⚠️ 高级设置仅供有经验的用户使用。错误的配置可能导致系统不稳定。")

    # 调试设置
    st.markdown("#### 调试设置")

    enable_debug = st.checkbox("启用调试模式", False)
    if enable_debug:
        debug_level = st.selectbox("调试级别", ["basic", "detailed", "verbose"], index=0)
        log_tensors = st.checkbox("记录张量信息", False)
        profile_performance = st.checkbox("性能剖析", False)

    # 实验性功能
    st.markdown("#### 实验性功能")

    experimental_features = st.multiselect(
        "启用实验性功能",
        ["分布式训练", "混合精度训练", "模型压缩", "自动调参", "强化课程学习"],
        default=[]
    )

    for feature in experimental_features:
        st.info(f"✅ 已启用: {feature}")

    # 重置设置
    st.markdown("#### 重置设置")

    if st.button("恢复默认设置", type="secondary"):
        st.session_state.clear()
        st.success("所有设置已恢复为默认值")
        st.rerun()

    # 导出/导入设置
    st.markdown("#### 设置管理")

    col_export, col_import = st.columns(2)

    with col_export:
        if st.button("导出设置", use_container_width=True):
            # 收集所有设置
            all_settings = {
                "system": st.session_state.get("system_settings", {}),
                "visualization": st.session_state.get("viz_settings", {}),
                "experiment": st.session_state.get("experiment_config", {})
            }

            # 转换为YAML
            settings_yaml = yaml.dump(all_settings, default_flow_style=False)

            st.download_button(
                label="下载设置文件",
                data=settings_yaml,
                file_name="tetris_rl_settings.yaml",
                mime="text/yaml"
            )

    with col_import:
        uploaded_settings = st.file_uploader("导入设置文件", type=["yaml", "yml"])
        if uploaded_settings is not None:
            if st.button("导入设置", use_container_width=True):
                try:
                    settings_data = yaml.safe_load(uploaded_settings)
                    if isinstance(settings_data, dict):
                        for key, value in settings_data.items():
                            st.session_state[f"{key}_settings"] = value
                        st.success("设置已成功导入")
                        st.rerun()
                    else:
                        st.error("设置文件格式不正确")
                except Exception as e:
                    st.error(f"设置导入失败: {e}")

# 底部说明
st.divider()
st.markdown("""
### 使用说明

1. **系统设置**: 配置日志、自动保存和硬件资源
2. **可视化设置**: 调整界面主题和渲染选项
3. **实验配置**: 设置实验参数和超参数
4. **高级设置**: 访问调试功能和实验性特性

### 提示

- 设置会自动保存到当前会话
- 可以导出设置以便在其他环境中使用
- 高级设置请谨慎修改
""")