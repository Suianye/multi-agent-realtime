"""WebSocket服务器 - 实时多AI工具协作"""
import asyncio
import json
import time
import websockets
from typing import Set, Dict
from agents import create_agents
from dispatcher import select_agent, analyze_task

class CollaborationServer:
    def __init__(self):
        self.clients: Set = set()
        self.agents = create_agents()
        self.running = False
    
    async def broadcast(self, message: dict):
        if self.clients:
            msg = json.dumps(message, ensure_ascii=False)
            await asyncio.gather(*[c.send(msg) for c in self.clients], return_exceptions=True)
    
    def make_log(self, source, target, message):
        return {"type": "log", "source": source, "target": target, "message": message}
    
    def make_status(self, agent_id, status, task=None):
        return {"type": "agent_status", "agent": agent_id, "status": status, "task": task}
    
    async def execute_task(self, task_data: dict):
        prompt = task_data.get("prompt", "")
        mode = task_data.get("mode", "auto")
        task_name = task_data.get("name", "未命名任务")
        
        await self.broadcast(self.make_log("👤 用户", "🎯 系统", f"提交任务: {task_name}"))
        
        task_type = analyze_task(prompt)
        await self.broadcast(self.make_log("🎯 调度器", "📊 分析", f"任务类型: {task_type}"))
        
        selected = select_agent(prompt, self.agents, mode)
        await self.broadcast(self.make_log("🎯 调度器", "📋 策略", f"模式: {mode}, 代理: {selected}"))
        
        results = []
        
        if mode in ("parallel", "compete"):
            # 并行执行
            tasks = []
            for agent_id in selected:
                agent = self.agents[agent_id]
                agent.status = "working"
                agent.current_task = task_name
                await self.broadcast(self.make_status(agent_id, "working", task_name))
                tasks.append(self.run_agent(agent, prompt))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, agent_id in enumerate(selected):
                agent = self.agents[agent_id]
                agent.status = "idle"
                agent.current_task = None
                await self.broadcast(self.make_status(agent_id, "idle"))
                
                result = results[i] if i < len(results) else "无结果"
                if isinstance(result, Exception):
                    result = f"错误: {result}"
                await self.broadcast({
                    "type": "task_result",
                    "agent": agent_id,
                    "result": str(result)[:500],
                    "duration": 0
                })
        else:
            # 串行执行
            for agent_id in selected:
                agent = self.agents[agent_id]
                agent.status = "working"
                agent.current_task = task_name
                await self.broadcast(self.make_status(agent_id, "working", task_name))
                
                try:
                    result = await self.run_agent(agent, prompt)
                    await self.broadcast({
                        "type": "task_result",
                        "agent": agent_id,
                        "result": str(result)[:500],
                        "duration": 0
                    })
                except Exception as e:
                    await self.broadcast(self.make_log("❌ 错误", agent_id, str(e)))
                
                agent.status = "idle"
                agent.current_task = None
                await self.broadcast(self.make_status(agent_id, "idle"))
        
        await self.broadcast(self.make_log("🎯 系统", "✅ 完成", f"任务 {task_name} 执行完成"))
    
    async def run_agent(self, agent, prompt):
        return await agent.execute(prompt, lambda s,t,m: asyncio.ensure_future(
            self.broadcast(self.make_log(f"{agent.icon} {s}", t, m))
        ))
    
    async def handler(self, websocket, path):
        self.clients.add(websocket)
        await self.broadcast(self.make_log("🎯 系统", "🌐 连接", f"新客户端连接"))
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get("type") == "execute_task":
                    asyncio.create_task(self.execute_task(data.get("task", {})))
        except:
            pass
        finally:
            self.clients.discard(websocket)
    
    async def start(self, host="0.0.0.0", port=8765):
        print(f"🚀 WebSocket服务器启动在 ws://{host}:{port}")
        async with websockets.serve(self.handler, host, port):
            await asyncio.Future()

if __name__ == "__main__":
    server = CollaborationServer()
    asyncio.run(server.start())
