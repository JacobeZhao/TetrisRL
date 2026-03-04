"""
HTML5 Canvas游戏渲染器
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import streamlit.components.v1 as components

from tetris_rl.ui.core.visualizer import GameRenderer, GameState, RenderConfig


class HTML5CanvasRenderer(GameRenderer):
    """HTML5 Canvas游戏渲染器"""

    def __init__(self, config: RenderConfig):
        self.config = config
        self._html_template = self._load_template()
        self._websocket_url = "ws://localhost:8765/ws/game"  # 默认WebSocket地址

    def _load_template(self) -> str:
        """加载HTML模板"""
        template_path = Path(__file__).parent / "static" / "templates" / "game_canvas.html"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")

        # 如果模板文件不存在，返回基本模板
        return self._get_basic_template()

    def _get_basic_template(self) -> str:
        """获取基本的HTML模板"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { margin: 0; padding: 0; background: #0c0c10; }
                .game-container {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                }
                #game-canvas {
                    border: 2px solid #2b2d3a;
                    border-radius: 4px;
                    background: #0c0c10;
                }
            </style>
        </head>
        <body>
            <div class="game-container">
                <canvas id="game-canvas"></canvas>
            </div>
            <script>
                // 游戏数据占位符
                const gameData = {{GAME_DATA}};
                const config = {{CONFIG_DATA}};

                // 基本的Canvas渲染
                const canvas = document.getElementById('game-canvas');
                const ctx = canvas.getContext('2d');

                // 调整Canvas大小
                function resizeCanvas() {
                    const container = canvas.parentElement;
                    const size = Math.min(container.clientWidth, container.clientHeight * 1.8);
                    canvas.width = size;
                    canvas.height = size / 1.8;
                    render();
                }

                // 渲染游戏
                function render() {
                    if (!gameData.board) return;

                    const cellSize = canvas.width / 10;
                    const colors = {
                        'T': '#FF00FF', 'I': '#00FFFF', 'O': '#FFFF00',
                        'L': '#FFA500', 'J': '#0000FF', 'S': '#00FF00', 'Z': '#FF0000',
                        'background': '#0c0c10', 'grid': '#2b2d3a'
                    };

                    // 清空画布
                    ctx.fillStyle = colors.background;
                    ctx.fillRect(0, 0, canvas.width, canvas.height);

                    // 绘制网格
                    if (config.showGrid) {
                        ctx.strokeStyle = colors.grid;
                        ctx.lineWidth = 1;

                        for (let x = 0; x <= 10; x++) {
                            ctx.beginPath();
                            ctx.moveTo(x * cellSize, 0);
                            ctx.lineTo(x * cellSize, canvas.height);
                            ctx.stroke();
                        }

                        for (let y = 0; y <= 20; y++) {
                            ctx.beginPath();
                            ctx.moveTo(0, y * cellSize);
                            ctx.lineTo(canvas.width, y * cellSize);
                            ctx.stroke();
                        }
                    }

                    // 绘制方块
                    for (let y = 0; y < gameData.board.length; y++) {
                        for (let x = 0; x < gameData.board[y].length; x++) {
                            const pieceId = gameData.board[y][x];
                            if (pieceId > 0) {
                                drawBlock(x, y, pieceId);
                            }
                        }
                    }

                    function drawBlock(x, y, pieceId) {
                        const pieceName = pieceIdToName(pieceId);
                        const color = colors[pieceName] || colors['T'];

                        ctx.fillStyle = color;
                        ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);

                        // 高光效果
                        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
                        ctx.fillRect(x * cellSize, y * cellSize, cellSize * 0.2, cellSize);
                        ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize * 0.2);

                        // 边框
                        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
                        ctx.lineWidth = 1;
                        ctx.strokeRect(x * cellSize, y * cellSize, cellSize, cellSize);
                    }

                    function pieceIdToName(id) {
                        const mapping = {1: 'I', 2: 'O', 3: 'T', 4: 'L', 5: 'J', 6: 'S', 7: 'Z'};
                        return mapping[id] || 'T';
                    }
                }

                // 初始渲染
                window.addEventListener('load', () => {
                    resizeCanvas();
                    window.addEventListener('resize', resizeCanvas);
                });
            </script>
        </body>
        </html>
        """

    def render(self, state: GameState, config: RenderConfig) -> str:
        """渲染为HTML组件"""
        # 转换游戏状态为JSON
        game_data = {
            "board": state.board,
            "currentPiece": state.current_piece,
            "nextPiece": state.next_piece,
            "score": state.score,
            "lines": state.lines_cleared,
            "level": state.level,
            "gameOver": state.game_over
        }

        config_data = {
            "cellSize": config.cell_size,
            "showGrid": config.show_grid,
            "showGhost": config.show_ghost_piece,
            "theme": config.theme
        }

        # 生成包含JavaScript的HTML
        html = self._html_template.replace(
            "{{GAME_DATA}}", json.dumps(game_data)
        ).replace(
            "{{CONFIG_DATA}}", json.dumps(config_data)
        )

        return html

    def update_config(self, config: RenderConfig) -> None:
        """更新配置"""
        self.config = config