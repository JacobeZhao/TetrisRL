"""
模型管理器组件
"""

import streamlit as st
from pathlib import Path
from typing import Optional, List, Dict, Any
import tempfile
import os


class ModelManager:
    def __init__(self, model_dir: str = "runs/tetris_ppo"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def render(self):
        """渲染模型管理器"""
        st.subheader("🤖 模型管理")

        # 模型列表
        st.markdown("#### 已保存的模型")
        model_files = self._list_model_files()

        if not model_files:
            st.info("没有找到已保存的模型")
        else:
            # 显示模型列表
            for model_file in model_files:
                self._render_model_item(model_file)

        # 模型操作
        st.divider()
        st.markdown("#### 模型操作")

        col1, col2, col3 = st.columns(3)

        with col1:
            self._render_upload_section()

        with col2:
            self._render_save_section()

        with col3:
            self._render_export_section()

    def _list_model_files(self) -> List[Path]:
        """列出模型文件"""
        model_files = []
        for ext in ["*.pt", "*.pth", "*.ckpt"]:
            model_files.extend(self.model_dir.glob(ext))

        # 按修改时间排序（最新的在前）
        model_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return model_files[:10]  # 只显示最近的10个

    def _render_model_item(self, model_file: Path):
        """渲染单个模型项"""
        file_size = model_file.stat().st_size / (1024 * 1024)  # MB
        modified_time = model_file.stat().st_mtime

        import time
        from datetime import datetime
        modified_str = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M:%S")

        with st.expander(f"{model_file.name} ({file_size:.2f} MB)"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"**修改时间**\n{modified_str}")

            with col2:
                if st.button("加载", key=f"load_{model_file.name}", use_container_width=True):
                    self._load_model(model_file)

            with col3:
                if st.button("删除", key=f"delete_{model_file.name}", use_container_width=True):
                    self._delete_model(model_file)

            # 下载按钮
            with open(model_file, 'rb') as f:
                st.download_button(
                    label="下载模型",
                    data=f,
                    file_name=model_file.name,
                    mime="application/octet-stream",
                    use_container_width=True
                )

    def _render_upload_section(self):
        """渲染上传区域"""
        st.markdown("**上传模型**")
        uploaded_file = st.file_uploader(
            "选择模型文件",
            type=["pt", "pth", "ckpt"],
            key="model_upload",
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            if st.button("上传并保存", use_container_width=True):
                self._save_uploaded_model(uploaded_file)

    def _render_save_section(self):
        """渲染保存区域"""
        st.markdown("**保存模型**")

        model_name = st.text_input(
            "模型名称",
            value=f"model_{st.session_state.get('update_count', 0)}",
            key="save_model_name",
            label_visibility="collapsed"
        )

        if st.button("保存当前模型", use_container_width=True):
            self._save_current_model(model_name)

    def _render_export_section(self):
        """渲染导出区域"""
        st.markdown("**导出模型**")

        export_format = st.selectbox(
            "导出格式",
            ["PyTorch (.pt)", "ONNX (.onnx)", "TensorFlow (.pb)"],
            key="export_format",
            label_visibility="collapsed"
        )

        if st.button("导出模型", use_container_width=True):
            self._export_model(export_format)

    def _load_model(self, model_path: Path):
        """加载模型"""
        try:
            # 这里应该调用实际的模型加载逻辑
            # 暂时使用占位符
            st.session_state.current_model = str(model_path)
            st.success(f"模型已加载: {model_path.name}")
            st.rerun()
        except Exception as e:
            st.error(f"模型加载失败: {e}")

    def _delete_model(self, model_path: Path):
        """删除模型"""
        try:
            model_path.unlink()
            st.success(f"模型已删除: {model_path.name}")
            st.rerun()
        except Exception as e:
            st.error(f"模型删除失败: {e}")

    def _save_uploaded_model(self, uploaded_file):
        """保存上传的模型"""
        try:
            save_path = self.model_dir / uploaded_file.name

            # 确保文件名唯一
            counter = 1
            while save_path.exists():
                name_parts = uploaded_file.name.rsplit('.', 1)
                new_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                save_path = self.model_dir / new_name
                counter += 1

            save_path.write_bytes(uploaded_file.getvalue())
            st.success(f"模型已保存: {save_path.name}")
            st.rerun()
        except Exception as e:
            st.error(f"模型保存失败: {e}")

    def _save_current_model(self, model_name: str):
        """保存当前模型"""
        try:
            # 这里应该调用实际的模型保存逻辑
            # 暂时使用占位符
            from tetris_rl.trainer.ppo_trainer import PPOTrainer

            if "trainer" in st.session_state:
                trainer: PPOTrainer = st.session_state.trainer
                save_path = trainer.save_checkpoint(tag=model_name)
                if save_path:
                    st.success(f"模型已保存: {save_path}")
                else:
                    st.error("模型保存失败: 训练器未初始化")
            else:
                # 创建演示文件
                import torch
                import tempfile

                demo_model = {
                    "metadata": {
                        "name": model_name,
                        "timestamp": st.session_state.get("last_update_time", "unknown"),
                        "version": "1.0"
                    },
                    "state_dict": {}
                }

                save_path = self.model_dir / f"{model_name}.pt"
                torch.save(demo_model, save_path)
                st.success(f"演示模型已保存: {save_path.name}")

            st.rerun()
        except Exception as e:
            st.error(f"模型保存失败: {e}")

    def _export_model(self, export_format: str):
        """导出模型"""
        try:
            if export_format == "PyTorch (.pt)":
                st.info("PyTorch格式已是默认格式，无需额外导出")
                return

            # 这里应该调用实际的模型导出逻辑
            # 暂时使用占位符
            if export_format == "ONNX (.onnx)":
                st.warning("ONNX导出功能尚未实现")
            elif export_format == "TensorFlow (.pb)":
                st.warning("TensorFlow导出功能尚未实现")

            st.info("导出功能正在开发中...")
        except Exception as e:
            st.error(f"模型导出失败: {e}")

    def get_model_info(self, model_path: Path) -> Dict[str, Any]:
        """获取模型信息"""
        try:
            import torch
            checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)

            info = {
                "path": str(model_path),
                "size_mb": model_path.stat().st_size / (1024 * 1024),
                "keys": list(checkpoint.keys()) if isinstance(checkpoint, dict) else ["Unknown"]
            }

            # 提取更多信息
            if isinstance(checkpoint, dict):
                if "metadata" in checkpoint:
                    info.update(checkpoint["metadata"])
                if "cfg" in checkpoint:
                    info["config"] = checkpoint["cfg"]

            return info
        except Exception as e:
            return {
                "path": str(model_path),
                "error": str(e)
            }