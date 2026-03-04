"""
WebSocket服务
用于实时游戏状态推送
"""

import asyncio
import websockets
import json
from typing import Set, Dict, Any, Optional, Callable
from tetris_rl.env.tetris_env import TetrisEnv


class GameWebSocketServer:
    """WebSocket服务器，用于实时游戏状态推送"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.game_env: Optional[TetrisEnv] = None
        self.message_handlers: Dict[str, Callable] = {}
        self._server: Optional[websockets.Server] = None

    def set_game_env(self, env: TetrisEnv) -> None:
        """设置游戏环境"""
        self.game_env = env

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """注册消息处理器"""
        self.message_handlers[message_type] = handler

    async def handler(self, websocket):
        """处理WebSocket连接"""
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        print(f"WebSocket客户端连接: {client_ip}")

        try:
            async for message in websocket:
                # 处理客户端消息
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print(f"WebSocket客户端断开: {client_ip}")
        finally:
            self.clients.remove(websocket)

    async def _handle_message(self, websocket, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type in self.message_handlers:
                await self.message_handlers[msg_type](data.get("data"))
            elif msg_type == "game_action":
                # 处理游戏动作
                await self._handle_game_action(websocket, data)
            elif msg_type == "get_state":
                # 获取当前游戏状态
                await self._send_game_state(websocket)
            else:
                print(f"未知消息类型: {msg_type}")

        except json.JSONDecodeError:
            print("消息JSON解析失败")
        except Exception as e:
            print(f"消息处理失败: {e}")

    async def _handle_game_action(self, websocket, data: Dict[str, Any]):
        """处理游戏动作"""
        if not self.game_env:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "游戏环境未初始化"
            }))
            return

        action = data.get("action")
        if action is None:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "未指定动作"
            }))
            return

        try:
            # 执行动作
            obs, reward, terminated, truncated, info = self.game_env.step(action)

            # 发送更新后的游戏状态
            game_state = self._build_game_state(obs, info, terminated)
            await websocket.send(json.dumps({
                "type": "game_update",
                "state": game_state
            }))

            # 如果游戏结束，重置环境
            if terminated:
                obs, info = self.game_env.reset()
                game_state = self._build_game_state(obs, info, False)
                await websocket.send(json.dumps({
                    "type": "game_reset",
                    "state": game_state
                }))

        except Exception as e:
            print(f"游戏动作执行失败: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"动作执行失败: {e}"
            }))

    async def _send_game_state(self, websocket):
        """发送当前游戏状态"""
        if not self.game_env:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "游戏环境未初始化"
            }))
            return

        try:
            # 获取当前状态
            obs = self.game_env._get_obs()
            info = self.game_env._get_info()
            game_state = self._build_game_state(obs, info, self.game_env.game.game_over)

            await websocket.send(json.dumps({
                "type": "game_state",
                "state": game_state
            }))
        except Exception as e:
            print(f"获取游戏状态失败: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"获取状态失败: {e}"
            }))

    def _build_game_state(self, obs, info, game_over: bool) -> Dict[str, Any]:
        """构建游戏状态数据"""
        if not self.game_env:
            return {}

        return {
            "board": self.game_env.game.get_board_with_active(),
            "score": self.game_env.game.score,
            "lines": self.game_env.game.lines_cleared,
            "level": self.game_env.game.level,
            "next_piece": self.game_env.game.next_piece.id if self.game_env.game.next_piece else 0,
            "game_over": game_over,
            "episode": self.game_env.game.episode,
            "actions": self.game_env.game.actions
        }

    async def broadcast(self, message_type: str, data: Any):
        """广播消息给所有客户端"""
        if not self.clients:
            return

        message = {"type": message_type, "data": data}
        message_str = json.dumps(message)

        await asyncio.gather(
            *[client.send(message_str) for client in self.clients]
        )

    async def start(self):
        """启动WebSocket服务器"""
        self._server = await websockets.serve(self.handler, self.host, self.port)
        print(f"WebSocket服务器启动于 ws://{self.host}:{self.port}")

        # 永久运行
        await asyncio.Future()

    async def stop(self):
        """停止WebSocket服务器"""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            print("WebSocket服务器已停止")

    def run_in_background(self):
        """在后台运行WebSocket服务器"""
        import threading

        def run_server():
            asyncio.run(self.start())

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        return thread


class SimpleWebSocketService:
    """简化的WebSocket服务，用于Streamlit集成"""

    def __init__(self, port: int = 8765):
        self.port = port
        self.server: Optional[GameWebSocketServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self, game_env: Optional[TetrisEnv] = None):
        """启动WebSocket服务"""
        if self.server:
            return

        import threading

        self.server = GameWebSocketServer(port=self.port)
        if game_env:
            self.server.set_game_env(game_env)

        def run():
            asyncio.run(self.server.start())

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        print(f"WebSocket服务已启动 (端口: {self.port})")

    def stop(self):
        """停止WebSocket服务"""
        if self.server:
            asyncio.run(self.server.stop())
            self.server = None
            self.thread = None
            print("WebSocket服务已停止")

    def is_running(self) -> bool:
        """检查服务是否运行"""
        return self.server is not None and self.thread is not None and self.thread.is_alive()

    def get_server(self) -> Optional[GameWebSocketServer]:
        """获取服务器实例"""
        return self.server