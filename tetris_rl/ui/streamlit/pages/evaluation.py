"""
评估页面
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="评估 - Tetris RL", page_icon="📈")

st.title("📈 评估")

# 页面描述
st.markdown("""
在此页面评估和比较不同模型的性能。您可以查看训练历史、分析模型表现，并生成评估报告。
""")

# 创建标签页
tab1, tab2, tab3, tab4 = st.tabs(["训练历史", "模型比较", "性能分析", "报告生成"])

with tab1:
    st.subheader("📊 训练历史分析")

    # 模拟训练历史数据
    @st.cache_data
    def load_training_history():
        import numpy as np
        import pandas as pd

        # 生成模拟数据
        n_points = 200
        updates = list(range(n_points))

        # 损失曲线（指数衰减 + 噪声）
        base_loss = 2.0 * np.exp(-np.array(updates) / 50)
        loss = base_loss + np.random.randn(n_points) * 0.2

        # 得分曲线（逐渐上升）
        base_score = 1000 * (1 - np.exp(-np.array(updates) / 30))
        score = base_score + np.random.randn(n_points) * 100

        # 奖励曲线
        reward = 0.5 * score / 100 + np.random.randn(n_points) * 0.1

        df = pd.DataFrame({
            "update": updates,
            "loss": loss,
            "score": score,
            "reward": reward,
            "policy_loss": loss * 0.7 + np.random.randn(n_points) * 0.1,
            "value_loss": loss * 0.3 + np.random.randn(n_points) * 0.05
        })

        return df

    df = load_training_history()

    # 选择要显示的指标
    metrics = st.multiselect(
        "选择指标",
        ["loss", "score", "reward", "policy_loss", "value_loss"],
        default=["loss", "score"]
    )

    if metrics:
        # 创建图表
        fig = go.Figure()

        colors = px.colors.qualitative.Set2
        for i, metric in enumerate(metrics):
            fig.add_trace(go.Scatter(
                x=df["update"],
                y=df[metric],
                name=metric,
                mode="lines",
                line=dict(color=colors[i % len(colors)], width=2),
                opacity=0.8
            ))

        fig.update_layout(
            title="训练曲线",
            xaxis_title="更新次数",
            yaxis_title="数值",
            height=500,
            template="plotly_dark",
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)

        # 统计数据
        st.subheader("📋 统计摘要")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("总更新次数", len(df))

        with col2:
            final_loss = df["loss"].iloc[-1]
            st.metric("最终损失", f"{final_loss:.4f}")

        with col3:
            max_score = df["score"].max()
            st.metric("最高得分", f"{max_score:.0f}")

        with col4:
            avg_reward = df["reward"].mean()
            st.metric("平均奖励", f"{avg_reward:.4f}")

        # 数据表格
        st.subheader("📄 原始数据")
        st.dataframe(df.tail(20), use_container_width=True)

with tab2:
    st.subheader("🤖 模型比较")

    # 模拟模型比较数据
    @st.cache_data
    def load_model_comparison():
        models = ["PPO (当前)", "PPO (基线)", "A2C", "DQN", "随机策略"]
        metrics_data = {
            "平均得分": [1250, 1100, 980, 850, 320],
            "最高得分": [2850, 2600, 2100, 1800, 650],
            "平均行数": [45, 38, 32, 28, 12],
            "训练时间(小时)": [12.5, 10.2, 8.7, 15.3, 0.0],
            "稳定性": [0.85, 0.82, 0.78, 0.65, 0.15]
        }

        df = pd.DataFrame(metrics_data, index=models)
        return df

    comparison_df = load_model_comparison()

    # 选择比较指标
    compare_metrics = st.multiselect(
        "选择比较指标",
        comparison_df.columns.tolist(),
        default=["平均得分", "最高得分"]
    )

    if compare_metrics:
        # 雷达图
        st.subheader("📊 模型性能雷达图")

        fig = go.Figure()

        for model in comparison_df.index:
            values = comparison_df.loc[model, compare_metrics].tolist()
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=compare_metrics,
                fill="toself",
                name=model
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(comparison_df[compare_metrics].max()) * 1.1]
                )),
            showlegend=True,
            height=500,
            template="plotly_dark"
        )

        st.plotly_chart(fig, use_container_width=True)

        # 柱状图比较
        st.subheader("📊 模型性能比较")

        selected_model = st.selectbox(
            "选择基准模型",
            comparison_df.index.tolist(),
            index=0
        )

        # 计算相对于基准模型的性能
        baseline = comparison_df.loc[selected_model]
        comparison_relative = comparison_df.div(baseline) * 100

        fig2 = go.Figure()
        for model in comparison_df.index:
            fig2.add_trace(go.Bar(
                x=compare_metrics,
                y=comparison_relative.loc[model, compare_metrics],
                name=model,
                text=comparison_relative.loc[model, compare_metrics].round(1),
                textposition="auto"
            ))

        fig2.update_layout(
            title=f"相对于{selected_model}的性能(%)",
            barmode="group",
            height=500,
            template="plotly_dark",
            yaxis_title="百分比(%)"
        )

        st.plotly_chart(fig2, use_container_width=True)

        # 详细数据
        st.subheader("📋 详细比较数据")
        st.dataframe(comparison_df, use_container_width=True)

with tab3:
    st.subheader("⚡ 性能分析")

    # 性能指标
    st.markdown("#### 关键性能指标")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("推理速度", "2.3ms/步", "+15%")
        st.caption("较上一版本提升")

    with col2:
        st.metric("内存使用", "1.2GB", "-8%")
        st.caption("较上一版本减少")

    with col3:
        st.metric("训练稳定性", "94%", "+5%")
        st.caption("成功率")

    # 瓶颈分析
    st.subheader("🔍 性能瓶颈分析")

    bottlenecks = {
        "数据预处理": 35,
        "模型推理": 25,
        "环境模拟": 20,
        "梯度计算": 15,
        "其他": 5
    }

    fig = px.pie(
        values=list(bottlenecks.values()),
        names=list(bottlenecks.keys()),
        title="计算时间分布",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # 优化建议
    st.subheader("💡 优化建议")

    suggestions = [
        "✅ 使用批处理进行数据预处理",
        "⏳ 实现模型量化以减少内存使用",
        "🔧 优化环境模拟逻辑",
        "🚀 考虑使用GPU加速训练",
        "📦 实现检查点压缩"
    ]

    for suggestion in suggestions:
        st.markdown(f"- {suggestion}")

with tab4:
    st.subheader("📄 评估报告生成")

    # 报告配置
    st.markdown("#### 报告配置")

    report_title = st.text_input("报告标题", "Tetris RL 模型评估报告")
    author = st.text_input("作者", "AI Lab")
    date_range = st.date_input("评估日期范围")

    # 包含内容
    st.markdown("#### 包含内容")
    include_sections = st.multiselect(
        "选择报告章节",
        ["执行摘要", "方法概述", "实验结果", "性能分析", "结论建议", "附录"],
        default=["执行摘要", "实验结果", "结论建议"]
    )

    # 生成报告
    if st.button("生成评估报告", type="primary", use_container_width=True):
        st.success("评估报告生成中...")

        # 模拟报告生成
        import time
        import tempfile

        with st.spinner("正在生成报告..."):
            time.sleep(2)

            # 创建模拟报告
            report_content = f"""
            # {report_title}

            **作者**: {author}
            **日期**: {date_range}
            **生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}

            ## 执行摘要

            本报告对Tetris RL模型进行了全面评估。主要发现包括：

            - 当前PPO模型在平均得分方面表现最佳
            - 模型推理速度较上一版本提升15%
            - 内存使用减少8%
            - 训练稳定性达到94%

            ## 详细结果

            详细实验结果请参考各评估页面。

            ## 结论与建议

            基于评估结果，建议：

            1. 继续优化PPO算法的超参数
            2. 实施批处理优化以提升性能
            3. 考虑模型量化以减少内存占用

            ---

            *本报告由Tetris RL评估系统自动生成*
            """

            # 提供下载
            st.download_button(
                label="下载报告 (PDF)",
                data=report_content,
                file_name=f"{report_title.replace(' ', '_')}.md",
                mime="text/markdown"
            )

            st.info("报告已生成，点击上方按钮下载。")

# 底部说明
st.divider()
st.markdown("""
### 使用说明

1. **训练历史**: 查看和分析训练过程中的各项指标
2. **模型比较**: 比较不同模型或版本的性能
3. **性能分析**: 分析模型的计算性能和瓶颈
4. **报告生成**: 生成完整的评估报告

### 提示

- 所有图表都是交互式的，可以缩放、平移
- 数据支持导出为CSV格式
- 报告可以自定义内容和格式
""")