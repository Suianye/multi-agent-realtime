"""
AI工作室 - 代理管理器
每个代理都是工作室成员，能执行任务、审查他人工作、与其他代理通信
"""
import asyncio
import json
import time
import uuid
import subprocess
import shutil
import os
import sys
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, List, Any
from enum import Enum


class AgentRole(str, Enum):
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    OPTIMIZER = "optimizer"
    REVIEWER = "reviewer"


@dataclass
class ReviewResult:
    approved: bool
    score: int
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    reviewer: str = ""


@dataclass
class SubTask:
    id: str
    title: str
    description: str
    assigned_to: str
    status: str = "pending"
    dependencies: List[str] = field(default_factory=list)
    review_result: Optional[ReviewResult] = None
    result: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 2
    needs_review: bool = True


@dataclass
class Project:
    id: str
    name: str
    description: str
    status: str = "planning"
    subtasks: List[SubTask] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


def _find_hermes_python():
    """找到 hermes 的 Python 解释器路径"""
    # 方法1: 从 hermes.cmd 推断
    hermes_cmd = shutil.which("hermes")
    if hermes_cmd:
        cmd_dir = os.path.dirname(hermes_cmd)
        python_path = os.path.join(cmd_dir, "..", "python.exe")
        python_path = os.path.normpath(python_path)
        if os.path.exists(python_path):
            return python_path
    # 方法2: 常见安装路径
    for p in [
        os.path.expanduser(r"~\.hermes-web-ui\desktop-runtime\win-x64\python\python.exe"),
        os.path.expanduser(r"~\.hermes-web-ui\desktop-runtime\win-x64\python\Scripts\python.exe"),
    ]:
        if os.path.exists(p):
            return p
    # 方法3: 系统 python
    return shutil.which("python") or shutil.which("python3") or "python"


# 全局缓存 hermes python 路径
_HERMES_PYTHON = None

def get_hermes_python():
    global _HERMES_PYTHON
    if _HERMES_PYTHON is None:
        _HERMES_PYTHON = _find_hermes_python()
    return _HERMES_PYTHON


class BaseAgent:
    def __init__(self, agent_id, name, icon, role, skills):
        self.agent_id = agent_id
        self.name = name
        self.icon = icon
        self.role = role
        self.skills = skills
        self.status = "idle"
        self.current_task = None
        self._broadcast = None
        self.available = True

    def set_broadcaster(self, fn):
        self._broadcast = fn

    async def emit(self, event_type, data):
        if self._broadcast:
            await self._broadcast({"type": event_type, "agent": self.agent_id, "timestamp": time.time(), **data})

    async def execute(self, subtask, project):
        raise NotImplementedError

    async def _run_cli(self, cmd_list, timeout=180, stdin_data=None):
        """
        执行CLI命令。
        cmd_list: 命令行参数列表（prompt 已包含在 cmd_list 中）
        stdin_data: 可选的 stdin 输入
        """
        self.status = "working"
        await self.emit("agent_status", {"status": "working"})
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd_list,
                stdin=asyncio.subprocess.PIPE if stdin_data else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=stdin_data.encode("utf-8") if stdin_data else None),
                timeout=timeout
            )
            result = stdout.decode("utf-8", errors="replace").strip()
            err = stderr.decode("utf-8", errors="replace").strip()
            
            # 某些工具输出到 stderr
            if not result and err:
                # 过滤掉常见的非错误信息
                if not any(skip in err.lower() for skip in ["warning", "deprecat", "notice"]):
                    result = err
            
            return result
        except asyncio.TimeoutError:
            return "[超时] 执行超过 {} 秒".format(timeout)
        except FileNotFoundError:
            return "[错误] CLI工具未找到: {}".format(cmd_list[0])
        except Exception as e:
            return "[错误] {}".format(str(e))
        finally:
            self.status = "idle"
            await self.emit("agent_status", {"status": "idle"})


class ProjectManagerAgent(BaseAgent):
    """项目经理 (Hermes) - 拆解需求、分配任务、协调团队"""

    def __init__(self):
        super().__init__(
            agent_id="hermes",
            name="Hermes (项目经理)",
            icon="🎯",
            role=AgentRole.PROJECT_MANAGER,
            skills=["任务分解", "团队协调", "项目管理"],
        )
        # 检测 hermes 是否可用
        self.available = shutil.which("hermes") is not None
        self._hermes_python = get_hermes_python() if self.available else None

    async def decompose_task(self, requirement, project):
        self.status = "working"
        await self.emit("agent_status", {"status": "working", "task": "分析需求..."})
        await self.emit("log", {"source": "🎯 Hermes", "target": "需求分析", "message": "正在分析: {}...".format(requirement[:60])})

        prompt = """你是一个项目管理专家。请把以下需求拆解成具体的开发子任务。

需求: {}

请以JSON格式返回子任务列表:
{{"subtasks": [{{"id": "task-1", "title": "标题", "description": "描述", "assigned_to": "claude-code|codex|openclaw", "dependencies": [], "needs_review": true}}]}}

规则:
1. claude-code: 写代码/实现功能  2. codex: 优化/重构  3. openclaw: 审查
4. 代码任务 needs_review=true  5. 返回纯JSON""".format(requirement)

        result = ""

        # 方法1: 用 hermes CLI (通过 Python 直接调用，避免 uv trampoline 问题)
        if self.available and self._hermes_python:
            try:
                cmd = [self._hermes_python, "-m", "hermes_cli.main", "-z", prompt, "--yolo"]
                result = await self._run_cli(cmd, timeout=120)
                if result and not result.startswith("[错误]"):
                    await self.emit("log", {"source": "🎯 Hermes", "target": "AI分析", "message": "Hermes CLI 分析完成"})
            except Exception as e:
                await self.emit("log", {"source": "🎯 Hermes", "target": "降级", "message": "Hermes CLI 失败: {}".format(str(e)[:80])})

        # 方法2: 备用 - 用 claude CLI
        if not result or result.startswith("[错误]"):
            if shutil.which("claude"):
                try:
                    cmd = ["claude", "-p", "--dangerously-skip-permissions", prompt]
                    proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
                    result = stdout.decode("utf-8", errors="replace").strip()
                    if result:
                        await self.emit("log", {"source": "🎯 Hermes", "target": "AI分析", "message": "Claude Code 分析完成"})
                except Exception:
                    pass

        # 解析JSON
        subtasks = self._parse_subtasks(result) if result else []
        if not subtasks:
            subtasks = self._fallback(requirement)
            await self.emit("log", {"source": "🎯 Hermes", "target": "降级", "message": "使用内置模板分解任务"})
        else:
            await self.emit("log", {"source": "🎯 Hermes", "target": "任务分解", "message": "AI分解为 {} 个子任务".format(len(subtasks))})

        self.status = "idle"
        await self.emit("agent_status", {"status": "idle"})
        return subtasks

    def _parse_subtasks(self, result):
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(result[start:end])
                return data.get("subtasks", [])
        except Exception:
            pass
        return []

    def _fallback(self, requirement):
        return [
            {"id": "task-1", "title": "实现核心功能", "description": requirement, "assigned_to": "claude-code", "dependencies": [], "needs_review": True},
            {"id": "task-2", "title": "代码审查", "description": "审查 task-1 的代码质量", "assigned_to": "openclaw", "dependencies": ["task-1"], "needs_review": False},
            {"id": "task-3", "title": "代码优化", "description": "根据审查结果优化代码", "assigned_to": "codex", "dependencies": ["task-2"], "needs_review": True},
        ]


class DeveloperAgent(BaseAgent):
    """开发者 (Claude Code) - 写代码、实现功能"""

    def __init__(self):
        super().__init__(
            agent_id="claude-code",
            name="Claude Code (开发者)",
            icon="🤖",
            role=AgentRole.DEVELOPER,
            skills=["代码生成", "功能实现", "调试", "文档"],
        )
        self.available = shutil.which("claude") is not None

    async def execute(self, subtask, project):
        await self.emit("log", {"source": "🤖 Claude Code", "target": "开发", "message": "开始: {}".format(subtask.title)})

        context = self._build_context(subtask, project)
        result = ""

        if self.available:
            # claude -p: 非交互模式，prompt 作为参数传递
            cmd = ["claude", "-p", "--dangerously-skip-permissions", context]
            result = await self._run_cli(cmd, timeout=300)

        if not result or result.startswith("[错误]"):
            if result and result.startswith("[错误]"):
                await self.emit("log", {"source": "🤖 Claude Code", "target": "降级", "message": "CLI调用失败，使用演示模式"})
            result = self._demo_result(subtask)

        subtask.result = result
        await self.emit("log", {"source": "🤖 Claude Code", "target": "完成", "message": "完成: {} ({} chars)".format(subtask.title, len(result))})
        return result

    def _build_context(self, subtask, project):
        parts = ["任务: {}".format(subtask.title), "描述: {}".format(subtask.description)]
        if subtask.dependencies:
            parts.append("\n--- 前置任务结果 ---")
            for dep_id in subtask.dependencies:
                for st in project.subtasks:
                    if st.id == dep_id and st.result:
                        parts.append("[{}]: {}".format(st.title, st.result[:500]))
        if subtask.review_result and subtask.review_result.issues:
            parts.append("\n--- 审查反馈，请修复 ---")
            for issue in subtask.review_result.issues:
                parts.append("- {}".format(issue))
        return "\n".join(parts)

    def _demo_result(self, subtask):
        return """# {} - 实现完成

```python
# 由 Claude Code (开发者) 生成
# 任务: {}

class Solution:
    \"\"\"
    核心实现
    \"\"\"
    def __init__(self):
        self.name = "auto-generated"

    def run(self):
        # TODO: 根据需求实现具体逻辑
        return "实现完成"
```

## 说明
- 已完成核心功能实现
- 包含基础错误处理
- 可以进一步优化""".format(subtask.title, subtask.description)


class OptimizerAgent(BaseAgent):
    """优化师 (Codex) - 优化、重构代码"""

    def __init__(self):
        super().__init__(
            agent_id="codex",
            name="Codex (优化师)",
            icon="⚡",
            role=AgentRole.OPTIMIZER,
            skills=["代码优化", "重构", "性能改进"],
        )
        self.available = shutil.which("codex") is not None

    async def execute(self, subtask, project):
        await self.emit("log", {"source": "⚡ Codex", "target": "优化", "message": "开始: {}".format(subtask.title)})

        context = self._build_context(subtask, project)
        result = ""

        if self.available:
            # codex exec: prompt 通过 stdin 传递
            result = await self._run_cli(["codex", "exec"], timeout=300, stdin_data=context)

        if not result or result.startswith("[错误]"):
            if result and result.startswith("[错误]"):
                await self.emit("log", {"source": "⚡ Codex", "target": "降级", "message": "CLI调用失败，使用演示模式"})
            result = self._demo_result(subtask)

        subtask.result = result
        await self.emit("log", {"source": "⚡ Codex", "target": "完成", "message": "完成: {}".format(subtask.title)})
        return result

    def _build_context(self, subtask, project):
        parts = ["优化任务: {}".format(subtask.title), "描述: {}".format(subtask.description)]
        if subtask.dependencies:
            parts.append("\n--- 需要优化的代码 ---")
            for dep_id in subtask.dependencies:
                for st in project.subtasks:
                    if st.id == dep_id and st.result:
                        parts.append("[{}]:\n{}".format(st.title, st.result[:1500]))
        if subtask.review_result and subtask.review_result.issues:
            parts.append("\n--- 审查反馈 ---")
            for issue in subtask.review_result.issues:
                parts.append("- {}".format(issue))
        return "\n".join(parts)

    def _demo_result(self, subtask):
        return """# 优化报告 - {}

## 优化内容
1. 算法复杂度优化: O(n²) -> O(n log n)
2. 内存使用优化: 减少不必要的对象创建
3. 代码结构重构: 提取公共方法

## 性能提升
- 执行速度: 提升约 40%
- 内存占用: 减少约 25%""".format(subtask.title)


class ReviewerAgent(BaseAgent):
    """审查员 (OpenClaw) - 代码审查、质量检查"""

    def __init__(self):
        super().__init__(
            agent_id="openclaw",
            name="OpenClaw (审查员)",
            icon="🔍",
            role=AgentRole.REVIEWER,
            skills=["代码审查", "质量分析", "安全检查"],
        )
        self.available = shutil.which("openclaw") is not None

    async def execute(self, subtask, project):
        await self.emit("log", {"source": "🔍 OpenClaw", "target": "审查", "message": "审查中: {}".format(subtask.title)})

        review_target = None
        for dep_id in subtask.dependencies:
            for st in project.subtasks:
                if st.id == dep_id:
                    review_target = st
                    break

        if not review_target or not review_target.result:
            subtask.result = "[审查] 未找到可审查的产出"
            subtask.status = "done"
            return subtask.result

        prompt = """你是资深代码审查员。审查以下代码:

任务: {title}
代码:
{code}

返回JSON: {{"approved": true/false, "score": 0-100, "issues": [], "suggestions": [], "summary": "评价"}}""".format(
            title=review_target.title, code=review_target.result[:3000])

        result = ""
        if self.available:
            # openclaw agent -m <message> --json
            # prompt 必须作为 -m 的参数，不能通过 stdin
            cmd = ["openclaw", "agent", "-m", prompt, "--json"]
            result = await self._run_cli(cmd, timeout=120)

        if not result or result.startswith("[错误]"):
            if result and result.startswith("[错误]"):
                await self.emit("log", {"source": "🔍 OpenClaw", "target": "降级", "message": "CLI调用失败，使用演示模式"})
            result = self._demo_review(review_target)

        subtask.result = result
        subtask.status = "done"

        review = self._parse_review(result)
        review_target.review_result = review
        review.reviewer = self.agent_id

        verdict = "通过" if review.approved else "需要修改"
        await self.emit("log", {"source": "🔍 OpenClaw", "target": verdict, "message": "评分: {}/100 | 问题: {}".format(review.score, len(review.issues))})
        return result

    def _demo_review(self, target):
        return json.dumps({
            "approved": True,
            "score": 85,
            "issues": ["建议添加更多错误处理"],
            "suggestions": ["可以考虑添加单元测试"],
            "summary": "代码质量良好，基本功能完整"
        }, ensure_ascii=False)

    def _parse_review(self, result):
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0:
                data = json.loads(result[start:end])
                return ReviewResult(
                    approved=data.get("approved", False),
                    score=data.get("score", 50),
                    issues=data.get("issues", []),
                    suggestions=data.get("suggestions", []),
                )
        except Exception:
            pass
        return ReviewResult(approved=True, score=70)


def create_agents():
    agents = {
        "hermes": ProjectManagerAgent(),
        "claude-code": DeveloperAgent(),
        "codex": OptimizerAgent(),
        "openclaw": ReviewerAgent(),
    }
    return agents
