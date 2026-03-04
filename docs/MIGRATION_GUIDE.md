# Tetris RL 可视化迁移指南

## 从PyQt6迁移到Streamlit Web UI（新架构）

### 为什么迁移？
1. **解决启动问题**：彻底避免PyQt6和matplotlib兼容性问题
2. **更好的跨平台支持**：只需浏览器，无需安装GUI库
3. **现代化架构**：模块化设计，易于扩展和维护
4. **实时交互**：WebSocket支持实时游戏状态推送
5. **多页面应用**：清晰的界面组织和导航

### 迁移步骤

#### 1. 备份现有配置和数据
```bash
# 备份训练数据
cp -r runs/tetris_ppo runs/tetris_ppo_backup

# 备份配置文件（如果有）
cp tetris_rl_config.yaml tetris_rl_config_backup.yaml
```

#### 2. 安装新依赖
```bash
# 更新requirements.txt已包含新依赖
pip install -r tetris_rl/requirements.txt

# 或手动安装新依赖
pip install websockets pyyaml plotly
```

#### 3. 运行迁移工具（可选）
```bash
# 自动迁移旧UI文件到legacy目录
python tools/migrate_ui.py

# 或手动检查迁移
python tools/migrate_ui.py --check
```

#### 4. 启动新UI
```bash
# 方法1：使用主入口点（推荐）
python -m tetris_rl.main --backend streamlit

# 方法2：直接运行Streamlit
streamlit run tetris_rl/ui/streamlit_app.py

# 方法3：指定端口
python -m tetris_rl.main --backend streamlit --port 8502

# 方法4：使用传统PyQt6（不推荐）
python -m tetris_rl.main --backend pyqt6
```

### 功能对比

| 功能 | PyQt6版本 | Streamlit新架构 | 状态 |
|------|-----------|---------------|------|
| 游戏演示 | ✅ | ✅ | 完全支持（HTML5 Canvas） |
| 实时训练曲线 | ✅ | ✅ | 完全支持（Chart.js/D3.js） |
| 训练控制 | ✅ | ✅ | 完全支持 |
| 模型管理 | ✅ | ✅ | 完全支持 |
| 性能监控 | ⚠️ | ✅ | 新增功能 |
| 多页面导航 | ❌ | ✅ | 新增功能 |
| 响应式设计 | ❌ | ✅ | 新增功能 |
| WebSocket实时通信 | ❌ | ✅ | 新增功能 |
| 主题切换 | ❌ | ✅ | 新增功能 |
| 导出报告 | ❌ | ✅ | 新增功能 |

### 新架构优势

#### 1. 模块化设计
- **核心抽象层**: 统一的渲染器接口 (`GameRenderer`, `ChartRenderer`, `UIController`)
- **多后端支持**: HTML5 Canvas, Matplotlib, PyQt6, 文本模式
- **工厂模式**: 动态后端创建和切换

#### 2. 实时功能
- **WebSocket服务器**: 实时游戏状态推送
- **双向通信**: 客户端控制与服务器状态更新
- **自动重连**: 网络中断时自动恢复连接

#### 3. 现代化Web界面
- **Streamlit框架**: 快速开发的Web应用框架
- **响应式布局**: 适配不同屏幕尺寸
- **多页面应用**: 清晰的功能组织
- **暗色主题**: 专业的视觉效果

#### 4. 增强的管理功能
- **训练服务**: 后台训练进程管理
- **模型服务**: 模型版本管理和导出
- **配置系统**: YAML配置文件支持
- **评估报告**: 自动生成训练报告

### 代码迁移指南

#### 导入语句更新

**旧代码 (PyQt6)**:
```python
from tetris_rl.ui.main_window import MainWindow
from tetris_rl.ui.game_canvas import GameCanvas
from tetris_rl.ui.plots import LivePlots
```

**新代码 (Streamlit)**:
```python
# 方法1：使用新架构
from tetris_rl.ui.core.visualizer import GameState, RenderConfig
from tetris_rl.ui.core.factory import BackendRegistry

# 方法2：向后兼容（不推荐）
from tetris_rl.ui.legacy.main_window import MainWindow  # 旧模块
```

#### 应用启动更新

**旧启动方式**:
```python
# main.py (旧)
from PyQt6.QtWidgets import QApplication
from tetris_rl.ui.main_window import MainWindow

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
```

**新启动方式**:
```python
# 方法1：使用统一入口
from tetris_rl.ui import launch_app
launch_app(backend="streamlit", port=8501)

# 方法2：直接运行Streamlit
import streamlit.web.cli as stcli
import sys
sys.argv = ["streamlit", "run", "tetris_rl/ui/streamlit_app.py"]
stcli.main()
```

#### 配置系统更新

**旧配置方式**:
```python
# 硬编码参数或自定义配置
```

**新配置方式**:
```python
from tetris_rl.ui.core.config import VisualizationConfig

# 从YAML文件加载
config = VisualizationConfig.from_yaml("config/viz_config.yaml")

# 或手动创建
config = VisualizationConfig(
    theme="dark",
    cell_size=30,
    show_grid=True,
    chart_max_points=1000
)

# 保存配置
config.save_default()
```

### 常见问题

#### 1. Q: 我还能使用PyQt6版本吗？
**A**: 可以，使用 `--backend pyqt6` 参数，但不推荐长期使用。PyQt6版本已标记为遗留代码，不再接收新功能更新。

#### 2. Q: 我的训练数据会丢失吗？
**A**: 不会，新架构使用相同的训练数据目录 (`runs/tetris_ppo`)。所有检查点文件完全兼容。

#### 3. Q: 需要重新训练模型吗？
**A**: 不需要，模型格式 (`*.pt`, `*.pth`) 完全兼容。新架构可以直接加载旧模型。

#### 4. Q: 如何访问旧UI代码？
**A**: 旧UI文件已移动到 `tetris_rl/ui/legacy/` 目录，可以通过 `from tetris_rl.ui.legacy import MainWindow` 导入。

#### 5. Q: WebSocket连接失败怎么办？
**A**: 检查端口8765是否被占用，或使用 `--port` 参数指定其他端口。防火墙可能阻止WebSocket连接。

#### 6. Q: Streamlit应用启动慢？
**A**: 首次启动会较慢，因为需要初始化组件。后续启动会利用缓存。

#### 7. Q: 如何自定义界面主题？
**A**: 在设置页面或通过 `VisualizationConfig` 配置主题、颜色和布局。

### 故障排除

#### 启动问题
```bash
# 检查依赖
pip list | grep -E "(streamlit|websockets|pyyaml|plotly)"

# 检查端口占用
netstat -ano | findstr :8501
netstat -ano | findstr :8765

# 清理Streamlit缓存
rm -rf ~/.streamlit/cache
```

#### 导入错误
```python
# 如果出现导入错误，确保路径正确
import sys
sys.path.insert(0, "/path/to/tetris_rl_project")
```

#### 性能问题
- **启用GPU**: 在设置中启用GPU加速
- **减少数据点**: 降低图表最大数据点数
- **关闭动画**: 降低动画速度或关闭动画

### 下一步

#### 短期优化
1. **性能优化**: Canvas渲染优化，减少内存使用
2. **移动端适配**: 响应式设计改进
3. **文档完善**: API文档和用户指南

#### 长期规划
1. **插件系统**: 支持第三方可视化插件
2. **云端部署**: 一键部署到云平台
3. **协作功能**: 多人观看和实时评论
4. **高级分析**: 训练过程深度分析

### 获取帮助

- **GitHub Issues**: [项目地址](https://github.com/yourusername/tetris-rl)
- **文档**: `docs/` 目录
- **示例代码**: `examples/` 目录
- **邮件支持**: yourusername@example.com

---

*迁移完成时间: 2024年3月*
*新架构版本: 2.0.0*
*祝您使用愉快！*