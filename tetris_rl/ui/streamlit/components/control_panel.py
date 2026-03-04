"""
控制面板组件
"""

import streamlit as st
from typing import Optional, Callable, Any
from tetris_rl.ui.core.visualizer import UIController
from tetris_rl.trainer.ppo_trainer import PPOConfig


class ControlPanel:
    def __init__(self, controller: UIController):
        self.controller = controller
        self._training_config: Optional[PPOConfig] = None

    def render(self):
        """渲染控制面板"""
        st.subheader("⚙️ 训练控制")

        # 训练参数配置
        with st.expander("训练参数", expanded=True):
            workers = st.slider("工作线程数", 1, 16, 4)
            learning_rate = st.number_input("学习率", 1e-5, 1e-2, 3e-4, format="%.6f")
            total_updates = st.number_input("总更新次数", 100, 100000, 10000)

            # 高级参数
            with st.expander("高级参数"):
                gamma = st.slider("折扣因子 (gamma)", 0.9, 0.999, 0.99, 0.001)
                gae_lambda = st.slider("GAE lambda", 0.9, 1.0, 0.95, 0.01)
                clip_param = st.slider("裁剪参数", 0.1, 0.3, 0.2, 0.01)
                entropy_coef = st.slider("熵系数", 0.0, 0.1, 0.01, 0.001)

            self._training_config = PPOConfig(
                workers=workers,
                learning_rate=learning_rate,
                total_updates=total_updates,
                gamma=gamma,
                gae_lambda=gae_lambda,
                clip_param=clip_param,
                entropy_coef=entropy_coef
            )

        # 控制按钮
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("▶️ 开始训练", use_container_width=True, type="primary"):
                if self._training_config:
                    self.controller.trigger_training_start(self._training_config)
                    st.success("训练已开始")
                else:
                    st.error("请先配置训练参数")

        with col2:
            if st.button("⏸️ 暂停", use_container_width=True):
                self.controller.trigger_training_pause()
                st.info("训练已暂停")

        with col3:
            if st.button("⏹️ 停止", use_container_width=True):
                self.controller.trigger_training_stop()
                st.warning("训练已停止")

        with col4:
            if st.button("🔄 重置", use_container_width=True):
                self.controller.trigger_training_reset()
                st.info("训练已重置")

        # 模型管理
        st.divider()
        st.subheader("💾 模型管理")

        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader("加载模型", type=["pt", "pth"], key="model_upload")
            if uploaded_file is not None:
                if st.button("加载模型", use_container_width=True):
                    # 保存上传的文件
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    self.controller.trigger_model_load(tmp_path)
                    st.success("模型已加载")

                    # 清理临时文件
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass

        with col2:
            if st.button("保存模型", use_container_width=True):
                save_path = self.controller.trigger_model_save("manual_save")
                if save_path:
                    st.success(f"模型已保存到: {save_path}")

        # 快速操作
        st.divider()
        st.subheader("⚡ 快速操作")

        quick_col1, quick_col2, quick_col3 = st.columns(3)
        with quick_col1:
            if st.button("运行演示", use_container_width=True):
                st.session_state.demo_mode = True
                st.info("演示模式已激活")

        with quick_col2:
            if st.button("性能测试", use_container_width=True):
                st.session_state.benchmark_mode = True
                st.info("性能测试模式已激活")

        with quick_col3:
            if st.button("导出报告", use_container_width=True):
                self._export_training_report()
                st.success("报告已导出")

    def _export_training_report(self):
        """导出训练报告"""
        # 这里可以生成训练报告
        import tempfile
        import json

        report_data = {
            "timestamp": st.session_state.get("last_update_time", "未知"),
            "config": self._training_config.__dict__ if self._training_config else {},
            "status": "训练报告"
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(report_data, f, indent=2)
            temp_path = f.name

        with open(temp_path, 'r') as f:
            st.download_button(
                label="下载报告",
                data=f.read(),
                file_name="training_report.json",
                mime="application/json"
            )

        import os
        try:
            os.unlink(temp_path)
        except:
            pass

    def render_simple(self, on_start: Callable, on_stop: Callable, on_reset: Callable):
        """简化版本的控制面板"""
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("开始训练", use_container_width=True, type="primary"):
                on_start()

        with col2:
            if st.button("停止训练", use_container_width=True):
                on_stop()

        with col3:
            if st.button("重置训练", use_container_width=True):
                on_reset()