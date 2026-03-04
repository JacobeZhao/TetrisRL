"""
Streamlit游戏画布组件
"""

import streamlit.components.v1 as components
import json
from pathlib import Path
from typing import Optional, Dict, Any

from tetris_rl.ui.core.visualizer import GameState


def game_canvas(game_state: GameState, config: Optional[Dict[str, Any]] = None,
                key: str = "game_canvas", height: int = 600) -> None:
    """
    Streamlit游戏画布自定义组件

    Args:
        game_state: 游戏状态
        config: 渲染配置
        key: 组件唯一键
        height: 组件高度
    """
    if config is None:
        config = {}

    # 加载HTML模板
    html_path = Path(__file__).parent.parent / "static" / "templates" / "game_canvas.html"
    if not html_path.exists():
        # 使用CanvasRenderer中的基本模板
        from ..canvas_renderer import HTML5CanvasRenderer
        from ...core.visualizer import RenderConfig

        render_config = RenderConfig(
            cell_size=config.get("cell_size", 30),
            show_grid=config.get("show_grid", True),
            show_ghost_piece=config.get("show_ghost", True),
            theme=config.get("theme", "dark")
        )

        renderer = HTML5CanvasRenderer(render_config)
        html_content = renderer.render(game_state, render_config)
    else:
        html_content = html_path.read_text(encoding="utf-8")

        # 准备数据
        game_data = {
            "board": game_state.board,
            "currentPiece": game_state.current_piece,
            "nextPiece": game_state.next_piece,
            "score": game_state.score,
            "lines": game_state.lines_cleared,
            "level": game_state.level,
            "gameOver": game_state.game_over
        }

        config_data = {
            "cellSize": config.get("cell_size", 30),
            "showGrid": config.get("show_grid", True),
            "showGhost": config.get("show_ghost", True),
            "theme": config.get("theme", "dark")
        }

        # 注入数据
        html_content = html_content.replace(
            "{{GAME_DATA}}",
            json.dumps(game_data, separators=(',', ':'))
        ).replace(
            "{{CONFIG_DATA}}",
            json.dumps(config_data, separators=(',', ':'))
        )

    # 渲染组件
    components.html(
        html_content,
        height=height,
        width=800,
        key=key
    )


def live_game_canvas(websocket_url: str = "ws://localhost:8765/ws/game",
                     config: Optional[Dict[str, Any]] = None,
                     key: str = "live_game_canvas", height: int = 600) -> None:
    """
    实时游戏画布组件，通过WebSocket接收更新

    Args:
        websocket_url: WebSocket服务器URL
        config: 渲染配置
        key: 组件唯一键
        height: 组件高度
    """
    if config is None:
        config = {}

    # 加载实时HTML模板
    html_path = Path(__file__).parent.parent / "static" / "templates" / "game_canvas.html"
    if not html_path.exists():
        # 创建基本实时模板
        html_content = create_live_template(websocket_url, config)
    else:
        html_content = html_path.read_text(encoding="utf-8")

        config_data = {
            "cellSize": config.get("cell_size", 30),
            "showGrid": config.get("show_grid", True),
            "showGhost": config.get("show_ghost", True),
            "theme": config.get("theme", "dark")
        }

        # 注入配置和WebSocket URL
        html_content = html_content.replace(
            "{{GAME_DATA}}", "{}"
        ).replace(
            "{{CONFIG_DATA}}",
            json.dumps(config_data, separators=(',', ':'))
        ).replace(
            "{{WS_URL}}", websocket_url
        )

    # 渲染组件
    components.html(
        html_content,
        height=height,
        width=800,
        key=key
    )


def create_live_template(websocket_url: str, config: Dict[str, Any]) -> str:
    """创建实时游戏模板"""
    config_json = json.dumps(config, separators=(',', ':'))

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Tetris RL Live</title>
        <style>
            body {{ margin: 0; padding: 0; background: #0c0c10; }}
            .game-container {{
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                padding: 20px;
                box-sizing: border-box;
            }}
            #game-canvas {{
                border: 2px solid #2b2d3a;
                border-radius: 8px;
                background: #0c0c10;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            }}
            .status {{
                position: absolute;
                top: 20px;
                left: 20px;
                color: #fff;
                background: rgba(43, 45, 58, 0.8);
                padding: 10px;
                border-radius: 4px;
                font-family: monospace;
            }}
        </style>
    </head>
    <body>
        <div class="game-container">
            <canvas id="game-canvas"></canvas>
            <div class="status" id="status">等待连接...</div>
        </div>

        <script>
            const config = {config_json};
            const wsUrl = "{websocket_url}";

            // 初始化Canvas
            const canvas = document.getElementById('game-canvas');
            const ctx = canvas.getContext('2d');
            let cellSize = 30;

            // 颜色定义
            const colors = {{
                'I': '#00FFFF', 'O': '#FFFF00', 'T': '#FF00FF',
                'L': '#FFA500', 'J': '#0000FF', 'S': '#00FF00', 'Z': '#FF0000',
                'background': '#0c0c10', 'grid': '#2b2d3a'
            }};

            // 游戏状态
            let gameState = {{ board: [] }};

            // 调整Canvas大小
            function resizeCanvas() {{
                const container = canvas.parentElement;
                const maxWidth = container.clientWidth - 40;
                const maxHeight = container.clientHeight - 40;

                const width = Math.min(maxWidth, maxHeight * 0.5);
                const height = width * 2;

                canvas.width = width;
                canvas.height = height;
                cellSize = width / 10;

                render();
            }}

            // 渲染游戏
            function render() {{
                if (!gameState.board || gameState.board.length === 0) return;

                // 清空画布
                ctx.fillStyle = colors.background;
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                // 绘制网格
                if (config.showGrid) {{
                    ctx.strokeStyle = colors.grid;
                    ctx.lineWidth = 1;

                    for (let x = 0; x <= 10; x++) {{
                        ctx.beginPath();
                        ctx.moveTo(x * cellSize, 0);
                        ctx.lineTo(x * cellSize, canvas.height);
                        ctx.stroke();
                    }}

                    for (let y = 0; y <= 20; y++) {{
                        ctx.beginPath();
                        ctx.moveTo(0, y * cellSize);
                        ctx.lineTo(canvas.width, y * cellSize);
                        ctx.stroke();
                    }}
                }}

                // 绘制方块
                for (let y = 0; y < gameState.board.length; y++) {{
                    for (let x = 0; x < gameState.board[y].length; x++) {{
                        const pieceId = gameState.board[y][x];
                        if (pieceId > 0) {{
                            drawBlock(x, y, pieceId);
                        }}
                    }}
                }}

                // 更新状态显示
                updateStatus();
            }}

            function drawBlock(x, y, pieceId) {{
                const pieceName = pieceIdToName(pieceId);
                const color = colors[pieceName] || colors['T'];

                ctx.fillStyle = color;
                ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);

                ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
                ctx.fillRect(x * cellSize, y * cellSize, cellSize * 0.2, cellSize);
                ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize * 0.2);

                ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
                ctx.lineWidth = 1;
                ctx.strokeRect(x * cellSize, y * cellSize, cellSize, cellSize);
            }}

            function pieceIdToName(id) {{
                const mapping = {{1: 'I', 2: 'O', 3: 'T', 4: 'L', 5: 'J', 6: 'S', 7: 'Z'}};
                return mapping[id] || 'T';
            }}

            function updateStatus() {{
                const statusEl = document.getElementById('status');
                if (gameState.gameOver) {{
                    statusEl.innerHTML = `游戏结束 | 得分: ${{gameState.score || 0}} | 等级: ${{gameState.level || 1}}`;
                    statusEl.style.color = '#ff6b6b';
                }} else {{
                    statusEl.innerHTML = `运行中 | 得分: ${{gameState.score || 0}} | 等级: ${{gameState.level || 1}}`;
                    statusEl.style.color = '#4ecdc4';
                }}
            }}

            // WebSocket连接
            function connectWebSocket() {{
                try {{
                    const ws = new WebSocket(wsUrl);

                    ws.onopen = function() {{
                        console.log('WebSocket连接已建立');
                        document.getElementById('status').textContent = '已连接';
                    }};

                    ws.onmessage = function(event) {{
                        try {{
                            const data = JSON.parse(event.data);
                            if (data.type === 'game_update' || data.type === 'game_state') {{
                                gameState = data.state;
                                render();
                            }}
                        }} catch (e) {{
                            console.error('消息解析失败:', e);
                        }}
                    }};

                    ws.onerror = function(error) {{
                        console.error('WebSocket错误:', error);
                        document.getElementById('status').textContent = '连接错误';
                    }};

                    ws.onclose = function() {{
                        console.log('WebSocket连接已关闭');
                        document.getElementById('status').textContent = '连接断开，3秒后重试...';
                        setTimeout(connectWebSocket, 3000);
                    }};
                }} catch (e) {{
                    console.error('WebSocket初始化失败:', e);
                    document.getElementById('status').textContent = '初始化失败';
                }}
            }}

            // 初始化
            window.addEventListener('load', function() {{
                resizeCanvas();
                window.addEventListener('resize', resizeCanvas);
                connectWebSocket();
            }});
        </script>
    </body>
    </html>
    """