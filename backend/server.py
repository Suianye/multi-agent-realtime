"""
AI工作室 - WebSocket服务器
"""
import asyncio
import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import websockets
from typing import Set
from agents import create_agents
from dispatcher import StudioDispatcher


class StudioServer:
    def __init__(self):
        self.clients: Set = set()
        self.agents = create_agents()
        self.dispatcher = StudioDispatcher(self.agents)
        self.dispatcher.set_broadcaster(self.broadcast)

    async def broadcast(self, message):
        if self.clients:
            msg = json.dumps(message, ensure_ascii=False, default=str)
            dead = set()
            for c in self.clients:
                try:
                    await c.send(msg)
                except Exception:
                    dead.add(c)
            self.clients -= dead

    async def handler(self, websocket):
        self.clients.add(websocket)
        await self.broadcast({"type": "log", "source": "系统", "target": "连接", "message": "新客户端连接 (共 {} 个)".format(len(self.clients))})

        # 发送代理状态 + 可用性
        for aid, agent in self.agents.items():
            await websocket.send(json.dumps({
                "type": "agent_status", "agent": aid, "status": agent.status, "available": agent.available
            }, ensure_ascii=False))

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle(data)
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)

    async def _handle(self, data):
        msg_type = data.get("type")

        if msg_type == "start_project":
            name = data.get("name", "未命名")
            req = data.get("requirement", "")
            if req:
                asyncio.create_task(self._run_project(name, req))

        elif msg_type == "execute_task":
            prompt = data.get("prompt", "")
            if prompt:
                asyncio.create_task(self._run_project(prompt[:30], prompt))

    async def _run_project(self, name, requirement):
        try:
            await self.dispatcher.start_project(name, requirement)
        except Exception as e:
            await self.broadcast({"type": "log", "source": "系统", "target": "错误", "message": "项目执行失败: {}".format(str(e)[:200])})
            await self.broadcast({"type": "phase_change", "phase": "error", "message": "项目执行出错"})

    async def start(self, host="0.0.0.0", port=8765):
        print("=" * 50)
        print("  AI工作室服务器")
        print("  WebSocket: ws://{}:{}".format(host, port))
        print("  前端: 打开 frontend/index.html")
        # 显示代理可用性
        for aid, agent in self.agents.items():
            status = "可用" if agent.available else "未安装(使用演示模式)"
            print("  {} {}: {}".format(agent.icon, agent.name, status))
        print("=" * 50)

        async with websockets.serve(self.handler, host, port):
            await asyncio.Future()


if __name__ == "__main__":
    server = StudioServer()
    asyncio.run(server.start())
