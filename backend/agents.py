"""代理管理器 - 封装4个AI工具的CLI调用"""
import asyncio
import json
import time
from typing import Optional, Callable, Awaitable

class BaseAgent:
    """代理基类"""
    def __init__(self, agent_id: str, name: str, icon: str):
        self.agent_id = agent_id
        self.name = name
        self.icon = icon
        self.status = "idle"
        self.current_task = None
    
    async def execute(self, prompt: str, on_log: Callable) -> str:
        raise NotImplementedError

class ClaudeCodeAgent(BaseAgent):
    def __init__(self):
        super().__init__("claude-code", "Claude Code", "🤖")
    
    async def execute(self, prompt: str, on_log: Callable) -> str:
        on_log("协调器", self.name, f"开始执行: {prompt[:30]}...")
        proc = await asyncio.create_subprocess_exec(
            "claude", "-p", prompt, "--dangerously-skip-permissions",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        result = stdout.decode("utf-8", errors="replace").strip()
        if not result and stderr:
            result = stderr.decode("utf-8", errors="replace").strip()
        return result

class CodexAgent(BaseAgent):
    def __init__(self):
        super().__init__("codex", "Codex", "⚡")
    
    async def execute(self, prompt: str, on_log: Callable) -> str:
        on_log("协调器", self.name, f"开始执行: {prompt[:30]}...")
        proc = await asyncio.create_subprocess_exec(
            "codex", "exec", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        result = stdout.decode("utf-8", errors="replace").strip()
        if not result and stderr:
            result = stderr.decode("utf-8", errors="replace").strip()
        return result

class OpenClawAgent(BaseAgent):
    def __init__(self):
        super().__init__("openclaw", "OpenClaw", "🔍")
    
    async def execute(self, prompt: str, on_log: Callable) -> str:
        on_log("协调器", self.name, f"开始执行: {prompt[:30]}...")
        proc = await asyncio.create_subprocess_exec(
            "openclaw", "agent", "-m", prompt, "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        result = stdout.decode("utf-8", errors="replace").strip()
        if not result and stderr:
            result = stderr.decode("utf-8", errors="replace").strip()
        return result

class HermesAgent(BaseAgent):
    def __init__(self):
        super().__init__("hermes", "Hermes Agent", "🎯")
    
    async def execute(self, prompt: str, on_log: Callable) -> str:
        on_log("协调器", self.name, f"开始执行: {prompt[:30]}...")
        proc = await asyncio.create_subprocess_exec(
            "hermes", "run", "--prompt", prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        result = stdout.decode("utf-8", errors="replace").strip()
        if not result and stderr:
            result = stderr.decode("utf-8", errors="replace").strip()
        return result

def create_agents():
    return {
        "claude-code": ClaudeCodeAgent(),
        "codex": CodexAgent(),
        "openclaw": OpenClawAgent(),
        "hermes": HermesAgent(),
    }
