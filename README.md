# Tetris RL (PPO + Ray + PyTorch + Gymnasium + 模块化可视化)

一个工程化的强化学习系统：使用 PPO 训练 Agent 学习经典俄罗斯方块，并提供**模块化可视化架构**，支持多种后端（Streamlit Web UI、PyQt6 桌面应用、CLI）用于实时训练控制、实时曲线显示与模型演示。

## 🚀 新架构亮点 (v2.0.0)

- **模块化可视化层**: 抽象渲染接口，支持多后端（HTML5 Canvas、Matplotlib、PyQt6）
- **Streamlit Web UI**: 现代化Web界面，多页面应用，响应式设计
- **实时WebSocket通信**: 双向实时游戏状态推送
- **工厂模式后端管理**: 动态切换渲染后端
- **统一配置系统**: YAML配置文件支持
- **增强的管理功能**: 训练服务、模型服务、评估报告

## 环境要求

- Python 3.11+
- Windows / Linux / macOS 均可（Ray 在不同平台依赖略有差异）

## 安装

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r tetris_rl/requirements.txt
```

## 🚀 快速开始

### 启动新架构 (推荐)

```bash
# 使用统一入口点，默认启动Streamlit Web UI
python -m tetris_rl.main

# 或明确指定后端
python -m tetris_rl.main --backend streamlit --port 8501

# 启动PyQt6桌面应用（传统）
python -m tetris_rl.main --backend pyqt6

# 启动命令行版本
python -m tetris_rl.main --backend cli
```

### 直接启动Streamlit

```bash
streamlit run tetris_rl/ui/streamlit_app.py
```

### 传统启动方式 (v1.x)

```bash
# PyQt6桌面应用（旧版本）
python -m tetris_rl.main --backend pyqt6
```

## Windows 常见问题：WinError 1114 / c10.dll 加载失败

如果启动时出现类似报错：

- `OSError: [WinError 1114] ... Error loading "...torch\\lib\\c10.dll" or one of its dependencies`

通常是系统运行库或 PyTorch 安装不完整导致，按下面顺序排查：

1) 安装 Microsoft Visual C++ Redistributable 2015-2022（x64）
2) 确认 Python 为 64-bit，建议优先使用 Python 3.11/3.12 官方发行版
3) 重新安装 PyTorch（先用 CPU 版本验证环境）

```bash
pip uninstall -y torch
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

4) 如果需要 GPU 训练：更新显卡驱动，并按 PyTorch 官方指引安装匹配的 CUDA 版本

## 训练说明

- 点击 **Start Training**：后台启动 PPO + Ray 并行采样训练；UI 不冻结。
- 点击 **Stop**：停止训练（会在一次更新结束后安全退出）。
- **Workers**：设置 Ray 采样并行 worker 数。
- **Speed**：控制 GUI 演示（agent play）速度。
- **Load Model**：加载 checkpoint 并自动用于演示。
- **Save Model**：保存当前模型到 `runs/tetris_ppo/checkpoints/manual_save.pt`。

## 工程结构

```
tetris_rl/
  core/                俄罗斯方块规则与逻辑
  env/                 Gymnasium 环境（特征工程状态 + 动作mask）
  model/               PPO Actor-Critic 网络（MLP 256-256）
  trainer/             PPO 训练器与 Ray 并行采样 worker
  ui/                  模块化可视化架构
    core/              核心抽象层（渲染器接口、配置、工厂）
    backends/          可视化后端实现
      html5/           HTML5 Canvas + JavaScript 后端
        static/        静态资源（HTML/CSS/JS）
        components/    Streamlit自定义组件
    streamlit/         Streamlit Web UI
      pages/           多页面应用
      components/      可复用组件
      services/        后台服务
    legacy/            遗留UI模块（向后兼容）
  main.py              统一入口点（支持多后端）
  requirements.txt     依赖列表
```

## 🆕 新架构特性 (v2.0.0)

### 模块化可视化层
- **抽象渲染接口**: `GameRenderer`, `ChartRenderer`, `UIController` 统一接口
- **多后端支持**: HTML5 Canvas (推荐), Matplotlib, PyQt6, 文本模式
- **工厂模式**: `BackendRegistry` 动态创建和管理后端
- **统一配置**: `VisualizationConfig` YAML配置文件支持

### Streamlit Web UI
- **多页面应用**: 训练、演示、评估、设置四个主要页面
- **实时交互**: WebSocket双向通信，实时游戏状态推送
- **响应式设计**: 适配桌面和移动设备
- **主题系统**: 暗色/亮色主题，可定制颜色方案

### 增强功能
- **训练服务**: 后台训练进程管理，状态监控
- **模型服务**: 模型版本管理，导出/导入功能
- **评估报告**: 自动生成训练分析报告
- **WebSocket服务器**: 实时通信支持，自动重连

### 向后兼容
- **遗留模块**: 旧UI文件移至 `tetris_rl/ui/legacy/`
- **统一入口**: `main.py` 支持多后端启动
- **数据兼容**: 训练数据和模型格式完全兼容

## 关键设计点

- 状态表示：特征工程（列高度/空洞/bumpiness/当前块&下一个块 one-hot 等），不使用像素输入。
- 动作空间：离散动作对应“枚举当前块的所有合法最终落点”；每一步直接执行一次落点放置。
- PPO：GAE、clipping、entropy bonus、mini-batch 更新、advantage normalization。
- Ray：多 worker 并行 rollout，主进程聚合后批量更新。
