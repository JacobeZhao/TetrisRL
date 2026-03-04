"""
图表组件
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional, Any
from tetris_rl.ui.core.visualizer import ChartRenderer
import pandas as pd


class LiveCharts:
    def __init__(self, chart_renderer: ChartRenderer):
        self.chart_renderer = chart_renderer
        self._data: Dict[str, List[Tuple[int, float]]] = {}

    def update_data(self, data: Dict[str, List[Tuple[int, float]]]):
        """更新图表数据"""
        self._data = data
        self.chart_renderer.update_data(data)

    def add_data_point(self, series_name: str, x: int, y: float):
        """添加单个数据点"""
        if series_name not in self._data:
            self._data[series_name] = []

        self._data[series_name].append((x, y))

        # 限制数据点数量
        max_points = 500
        if len(self._data[series_name]) > max_points:
            self._data[series_name] = self._data[series_name][-max_points:]

        self.chart_renderer.update_data(self._data)

    def render(self):
        """渲染图表"""
        st.subheader("📊 训练曲线")

        if not self._data:
            st.info("等待训练数据...")
            return

        # 使用图表渲染器
        chart_output = self.chart_renderer.render()

        if isinstance(chart_output, str) and chart_output.startswith("<"):
            # HTML图表
            st.components.v1.html(chart_output, height=400)
        else:
            # 回退到Streamlit原生图表
            self._render_fallback()

        # 数据统计
        self._render_statistics()

    def _render_fallback(self):
        """回退到Streamlit原生图表"""
        # 转换为DataFrame
        df_data = {}
        for series_name, points in self._data.items():
            if points:
                xs, ys = zip(*points)
                df_data[f"{series_name}_x"] = xs
                df_data[f"{series_name}_y"] = ys

        if df_data:
            # 创建标签页
            tab1, tab2, tab3 = st.tabs(["损失曲线", "得分曲线", "原始数据"])

            with tab1:
                loss_data = {}
                for series in ["loss", "loss_policy", "loss_value", "loss_entropy"]:
                    if series in self._data and self._data[series]:
                        loss_data[series] = self._data[series]

                if loss_data:
                    loss_df = pd.DataFrame({
                        "更新次数": [p[0] for p in loss_data.get("loss", [])],
                        "总损失": [p[1] for p in loss_data.get("loss", [])],
                        "策略损失": [p[1] for p in loss_data.get("loss_policy", [])],
                        "价值损失": [p[1] for p in loss_data.get("loss_value", [])]
                    })
                    st.line_chart(loss_df.set_index("更新次数"))

            with tab2:
                score_data = {}
                for series in ["score", "mean_episode_score", "max_episode_score"]:
                    if series in self._data and self._data[series]:
                        score_data[series] = self._data[series]

                if score_data:
                    score_df = pd.DataFrame({
                        "更新次数": [p[0] for p in score_data.get("score", [])],
                        "平均得分": [p[1] for p in score_data.get("mean_episode_score", [])],
                        "最大得分": [p[1] for p in score_data.get("max_episode_score", [])]
                    })
                    st.line_chart(score_df.set_index("更新次数"))

            with tab3:
                st.dataframe(self._create_dataframe(), use_container_width=True)

    def _create_dataframe(self) -> pd.DataFrame:
        """创建DataFrame用于显示"""
        max_len = max(len(points) for points in self._data.values()) if self._data else 0

        data = {"更新次数": list(range(max_len))}
        for series_name, points in self._data.items():
            values = [p[1] for p in points]
            # 填充不足的长度
            if len(values) < max_len:
                values = values + [None] * (max_len - len(values))
            data[series_name] = values

        return pd.DataFrame(data)

    def _render_statistics(self):
        """渲染数据统计"""
        st.subheader("📈 统计信息")

        if not self._data:
            return

        cols = st.columns(4)

        with cols[0]:
            total_points = sum(len(points) for points in self._data.values())
            st.metric("总数据点", total_points)

        with cols[1]:
            series_count = len(self._data)
            st.metric("数据系列", series_count)

        with cols[2]:
            # 计算最新损失值
            latest_loss = None
            for series in ["loss", "loss_policy", "loss_value"]:
                if series in self._data and self._data[series]:
                    latest_loss = self._data[series][-1][1] if latest_loss is None else latest_loss
            if latest_loss is not None:
                st.metric("最新损失", f"{latest_loss:.4f}")

        with cols[3]:
            # 计算最新得分
            latest_score = None
            for series in ["score", "mean_episode_score"]:
                if series in self._data and self._data[series]:
                    latest_score = self._data[series][-1][1] if latest_score is None else latest_score
            if latest_score is not None:
                st.metric("最新得分", f"{latest_score:.0f}")

    @staticmethod
    def create_demo_data() -> Dict[str, List[Tuple[int, float]]]:
        """创建演示数据"""
        import random
        import math

        data = {
            "loss": [],
            "loss_policy": [],
            "loss_value": [],
            "score": [],
            "mean_episode_score": [],
            "max_episode_score": []
        }

        for i in range(100):
            # 模拟损失曲线（指数衰减）
            base_loss = 2.0 * math.exp(-i / 50)
            loss = base_loss + random.random() * 0.3

            policy_loss = base_loss * 0.7 + random.random() * 0.2
            value_loss = base_loss * 0.3 + random.random() * 0.1

            # 模拟得分曲线（逐渐上升）
            base_score = 1000 * (1 - math.exp(-i / 30))
            score = base_score + random.random() * 200

            mean_score = base_score + random.random() * 100
            max_score = base_score * 1.5 + random.random() * 300

            data["loss"].append((i, loss))
            data["loss_policy"].append((i, policy_loss))
            data["loss_value"].append((i, value_loss))
            data["score"].append((i, score))
            data["mean_episode_score"].append((i, mean_score))
            data["max_episode_score"].append((i, max_score))

        return data