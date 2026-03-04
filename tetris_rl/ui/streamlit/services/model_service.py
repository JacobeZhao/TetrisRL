"""
模型服务
"""

import streamlit as st
from pathlib import Path
from typing import Optional, Dict, Any, List
import torch
import tempfile


class ModelService:
    """模型服务"""

    def __init__(self, model_dir: str = "runs/tetris_ppo"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.current_model: Optional[Dict[str, Any]] = None

    def load_model(self, model_path: Path) -> bool:
        """加载模型"""
        try:
            checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
            self.current_model = {
                "path": str(model_path),
                "checkpoint": checkpoint,
                "metadata": checkpoint.get("metadata", {}),
                "config": checkpoint.get("cfg", {})
            }

            # 更新会话状态
            st.session_state.current_model = self.current_model
            return True
        except Exception as e:
            st.error(f"模型加载失败: {e}")
            return False

    def save_model(self, tag: str, model_data: Optional[Dict[str, Any]] = None) -> Optional[Path]:
        """保存模型"""
        try:
            if model_data is None:
                model_data = self.current_model

            if model_data is None:
                st.error("没有可保存的模型数据")
                return None

            # 生成文件名
            timestamp = st.session_state.get("last_update_time", "unknown").replace(":", "-")
            filename = f"model_{tag}_{timestamp}.pt"
            save_path = self.model_dir / filename

            # 确保文件名唯一
            counter = 1
            while save_path.exists():
                filename = f"model_{tag}_{timestamp}_{counter}.pt"
                save_path = self.model_dir / filename
                counter += 1

            # 保存模型
            torch.save(model_data.get("checkpoint", {}), save_path)
            return save_path
        except Exception as e:
            st.error(f"模型保存失败: {e}")
            return None

    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有模型"""
        models = []
        for ext in ["*.pt", "*.pth", "*.ckpt"]:
            for model_file in self.model_dir.glob(ext):
                try:
                    info = self.get_model_info(model_file)
                    models.append(info)
                except:
                    # 跳过无法读取的模型文件
                    pass

        # 按修改时间排序（最新的在前）
        models.sort(key=lambda x: x.get("modified_time", 0), reverse=True)
        return models

    def get_model_info(self, model_path: Path) -> Dict[str, Any]:
        """获取模型信息"""
        try:
            stat = model_path.stat()
            checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)

            info = {
                "path": str(model_path),
                "name": model_path.name,
                "size_mb": stat.st_size / (1024 * 1024),
                "modified_time": stat.st_mtime,
                "has_state_dict": "state_dict" in checkpoint or "model_state_dict" in checkpoint,
                "has_config": "cfg" in checkpoint or "config" in checkpoint
            }

            # 提取元数据
            if isinstance(checkpoint, dict):
                if "metadata" in checkpoint:
                    info.update(checkpoint["metadata"])
                if "cfg" in checkpoint:
                    info["config"] = checkpoint["cfg"]

            return info
        except Exception as e:
            return {
                "path": str(model_path),
                "name": model_path.name,
                "error": str(e)
            }

    def delete_model(self, model_path: Path) -> bool:
        """删除模型"""
        try:
            model_path.unlink()
            return True
        except Exception as e:
            st.error(f"模型删除失败: {e}")
            return False

    def export_model(self, model_path: Path, export_format: str) -> Optional[Path]:
        """导出模型到其他格式"""
        try:
            if export_format == "onnx":
                return self._export_to_onnx(model_path)
            elif export_format == "tensorflow":
                return self._export_to_tensorflow(model_path)
            else:
                st.error(f"不支持的导出格式: {export_format}")
                return None
        except Exception as e:
            st.error(f"模型导出失败: {e}")
            return None

    def _export_to_onnx(self, model_path: Path) -> Optional[Path]:
        """导出为ONNX格式"""
        try:
            # 这里应该实现实际的ONNX导出逻辑
            # 暂时返回占位符
            st.warning("ONNX导出功能尚未实现")
            return None
        except Exception as e:
            st.error(f"ONNX导出失败: {e}")
            return None

    def _export_to_tensorflow(self, model_path: Path) -> Optional[Path]:
        """导出为TensorFlow格式"""
        try:
            # 这里应该实现实际的TensorFlow导出逻辑
            # 暂时返回占位符
            st.warning("TensorFlow导出功能尚未实现")
            return None
        except Exception as e:
            st.error(f"TensorFlow导出失败: {e}")
            return None

    def create_demo_model(self) -> Dict[str, Any]:
        """创建演示模型"""
        import time

        demo_checkpoint = {
            "metadata": {
                "name": "demo_model",
                "description": "演示模型",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0.0"
            },
            "cfg": {
                "workers": 4,
                "learning_rate": 3e-4,
                "total_updates": 10000
            },
            "state_dict": {
                "demo_layer.weight": torch.randn(10, 20),
                "demo_layer.bias": torch.randn(20)
            }
        }

        return {
            "path": "demo_model.pt",
            "checkpoint": demo_checkpoint,
            "metadata": demo_checkpoint["metadata"],
            "config": demo_checkpoint["cfg"]
        }


def get_or_create_model_service() -> ModelService:
    """获取或创建模型服务（Streamlit会话状态）"""
    if "model_service" not in st.session_state:
        st.session_state.model_service = ModelService()

    return st.session_state.model_service