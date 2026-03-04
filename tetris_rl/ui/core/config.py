"""
统一配置系统
管理可视化相关的所有配置
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import yaml
from pathlib import Path


@dataclass
class VisualizationConfig:
    """可视化统一配置"""

    # 通用配置
    theme: str = "dark"
    fps: int = 60
    render_quality: str = "high"  # low, medium, high, ultra

    # 游戏渲染配置
    cell_size: int = 30
    show_grid: bool = True
    show_ghost_piece: bool = True
    animation_speed: float = 1.0

    # 图表配置
    chart_max_points: int = 500
    chart_update_interval: float = 1.0
    chart_theme: str = "dark"

    # 后端特定配置
    backend_specific: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VisualizationConfig:
        """从字典创建配置实例"""
        # 提取已知字段
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        config_data = {}
        backend_data = {}

        for key, value in data.items():
            if key in known_fields:
                config_data[key] = value
            else:
                backend_data[key] = value

        config = cls(**config_data)
        config.backend_specific = backend_data
        return config

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 合并后端特定配置
        data.update(self.backend_specific)
        return data

    @classmethod
    def from_yaml(cls, path: str | Path) -> VisualizationConfig:
        """从YAML文件加载配置"""
        path = Path(path)
        if not path.exists():
            # 返回默认配置
            return cls()

        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        return cls.from_dict(data)

    def to_yaml(self, path: str | Path) -> None:
        """保存配置到YAML文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self.to_dict()
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    @classmethod
    def get_default_path(cls) -> Path:
        """获取默认配置文件路径"""
        return Path.home() / ".tetris_rl" / "viz_config.yaml"

    def save_default(self) -> None:
        """保存到默认配置文件路径"""
        self.to_yaml(self.get_default_path())

    @classmethod
    def load_default(cls) -> VisualizationConfig:
        """从默认配置文件加载"""
        return cls.from_yaml(cls.get_default_path())