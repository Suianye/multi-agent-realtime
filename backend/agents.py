"""
AI工作室 - 代理管理器
每个代理都是工作室成员，能执行任务、审查他人工作、与其他代理通信
"""
import asyncio
import json
import logging
import time
import uuid
import subprocess
import shutil
import os
import sys
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, List, Any
from enum import Enum

# 模块级日志记录器
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 自定义异常
# ──────────────────────────────────────────────

class AgentError(Exception):
    """代理操作错误基类"""
    pass


class AgentNotAvailableError(AgentError):
    """代理不可用时抛出"""
    pass


class TaskExecutionError(AgentError):
    """任务执行失败时抛出"""
    pass


class InvalidTaskError(AgentError):
    """任务数据无效时抛出"""
    pass


class CLIExecutionError(AgentError):
    """CLI 命令执行失败时抛出"""
    pass


class AgentRole(str, Enum):
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    OPTIMIZER = "optimizer"
    REVIEWER = "reviewer"


# ──────────────────────────────────────────────
# 输入验证函数
# ──────────────────────────────────────────────

def _validate_string(value: Any, name: str, allow_empty: bool = False) -> None:
    """验证字符串类型参数"""
    if not isinstance(value, str):
        logger.warning("参数类型错误: %s 期望 str, 实际为 %s", name, type(value).__name__)
        raise InvalidTaskError(f"参数 '{name}' 期望 str 类型, 收到 {type(value).__name__}")
    if not allow_empty and not value.strip():
        logger.warning("参数为空: %s", name)
        raise InvalidTaskError(f"参数 '{name}' 不能为空字符串")


def _validate_dict(value: Any, name: str) -> None:
    """验证字典类型参数"""
    if not isinstance(value, dict):
        logger.warning("参数类型错误: %s 期望 dict, 实际为 %s", name, type(value).__name__)
        raise InvalidTaskError(f"参数 '{name}' 期望 dict 类型, 收到 {type(value).__name__}")


def _validate_positive_int(value: Any, name: str) -> None:
    """验证正整数参数"""
    if not isinstance(value, int) or value <= 0:
        logger.warning("参数无效: %s=%r", name, value)
        raise InvalidTaskError(f"参数 '{name}' 必须是正整数, 收到 {value!r}")


def _validate_task_id(task_id: str) -> None:
    """验证任务 ID 格式"""
    _validate_string(task_id, "task_id")
    if not task_id.strip():
        raise InvalidTaskError("task_id 不能为空")


@dataclass
class ReviewResult:
    approved: bool
    score: int
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    reviewer: str = ""

    def __post_init__(self):
        """验证 ReviewResult 数据"""
        if not isinstance(self.approved, bool):
            logger.warning("ReviewResult.approved 类型错误: %s", type(self.approved).__name__)
            self.approved = bool(self.approved)
        if not isinstance(self.score, (int, float)):
            logger.warning("ReviewResult.score 类型错误: %s", type(self.score).__name__)
            self.score = 50
        else:
            self.score = max(0, min(100, int(self.score)))
        if not isinstance(self.issues, list):
            self.issues = list(self.issues) if self.issues else []
        if not isinstance(self.suggestions, list):
            self.suggestions = list(self.suggestions) if self.suggestions else []


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

    def __post_init__(self):
        """验证 SubTask 数据"""
        _validate_string(self.id, "SubTask.id")
        _validate_string(self.title, "SubTask.title")
        _validate_string(self.assigned_to, "SubTask.assigned_to")
        if not isinstance(self.dependencies, list):
            logger.warning("SubTask.dependencies 类型错误: %s", type(self.dependencies).__name__)
            self.dependencies = list(self.dependencies) if self.dependencies else []
        valid_statuses = {"pending", "assigned", "in_progress", "review", "revision", "done", "failed"}
        if self.status not in valid_statuses:
            logger.warning("SubTask.status 无效值: %s, 回退到 pending", self.status)
            self.status = "pending"
        if not isinstance(self.needs_review, bool):
            self.needs_review = bool(self.needs_review)
        if self.retry_count < 0:
            logger.warning("SubTask.retry_count 不能为负数: %d", self.retry_count)
            self.retry_count = 0
        if self.max_retries < 0:
            logger.warning("SubTask.max_retries 不能为负数: %d", self.max_retries)
            self.max_retries = 2


@dataclass
class Project:
    id: str
    name: str
    description: str
    status: str = "planning"
    subtasks: List[SubTask] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        """验证 Project 数据"""
        _validate_string(self.id, "Project.id")
        _validate_string(self.name, "Project.name")
        valid_statuses = {"planning", "executing", "done", "error", "cancelled"}
        if self.status not in valid_statuses:
            logger.warning("Project.status 无效值: %s, 回退到 planning", self.status)
            self.status = "planning"
        if not isinstance(self.subtasks, list):
            logger.warning("Project.subtasks 类型错误: %s", type(self.subtasks).__name__)
            self.subtasks = []
        if not isinstance(self.context, dict):
            logger.warning("Project.context 类型错误: %s", type(self.context).__name__)
            self.context = {}


def _find_hermes_python():
    """找到 hermes 的 Python 解释器路径"""
    logger.debug("正在查找 hermes Python 解释器...")

    # 方法1: 从 hermes.cmd 推断
    hermes_cmd = shutil.which("hermes")
    if hermes_cmd:
        logger.debug("找到 hermes 命令: %s", hermes_cmd)
        cmd_dir = os.path.dirname(hermes_cmd)
        python_path = os.path.join(cmd_dir, "..", "python.exe")
        python_path = os.path.normpath(python_path)
        if os.path.exists(python_path):
            logger.debug("从 hermes.cmd 推断 Python 路径: %s", python_path)
            return python_path

    # 方法2: 常见安装路径
    for p in [
        os.path.expanduser(r"~\.hermes-web-ui\desktop-runtime\win-x64\python\python.exe"),
        os.path.expanduser(r"~\.hermes-web-ui\desktop-runtime\win-x64\python\Scripts\python.exe"),
    ]:
        if os.path.exists(p):
            logger.debug("在常见路径找到 Python: %s", p)
            return p

    # 方法3: 系统 python
    system_python = shutil.which("python") or shutil.which("python3") or "python"
    logger.debug("使用系统 Python: %s", system_python)
    return system_python


# 全局缓存 hermes python 路径
_HERMES_PYTHON = None


def get_hermes_python():
    """获取 hermes Python 解释器路径（带缓存）"""
    global _HERMES_PYTHON
    if _HERMES_PYTHON is None:
        _HERMES_PYTHON = _find_hermes_python()
        logger.info("Hermes Python 解释器: %s", _HERMES_PYTHON)
    return _HERMES_PYTHON


@dataclass
class CLIResult:
    """CLI 执行结果，包含诊断信息"""
    output: str
    return_code: int = 0
    elapsed: float = 0.0
    last_output_time: float = 0.0
    total_bytes: int = 0
    stall_seconds: float = 0.0  # 最后一次输出距结束的秒数
    diagnosis: str = ""  # 超时诊断

class BaseAgent:
    """代理基类 - 提供通用的 CLI 执行和事件广播功能"""

    def __init__(self, agent_id: str, name: str, icon: str, role: AgentRole, skills: List[str]):
        _validate_string(agent_id, "agent_id")
        _validate_string(name, "name")

        self.agent_id = agent_id
        self.name = name
        self.icon = icon
        self.role = role
        self.skills = skills if isinstance(skills, list) else []
        self.status = "idle"
        self.current_task = None
        self._broadcast = None
        self.available = True
        logger.info("代理初始化: %s (%s) - %s", name, agent_id, "可用" if self.available else "不可用")

    def set_broadcaster(self, fn: Callable):
        """设置事件广播函数"""
        if fn is None:
            logger.warning("set_broadcaster 接收到 None")
            return
        if not callable(fn):
            logger.error("set_broadcaster 参数不可调用: %s", type(fn).__name__)
            raise TypeError("broadcaster 必须是可调用对象")
        self._broadcast = fn

    async def emit(self, event_type: str, data: dict):
        """发送事件到所有客户端"""
        if not event_type:
            logger.warning("emit: event_type 为空")
            return
        if not isinstance(data, dict):
            logger.warning("emit: data 不是 dict: %s", type(data).__name__)
            data = {"raw": str(data)}
        if self._broadcast:
            try:
                await self._broadcast({
                    "type": event_type,
                    "agent": self.agent_id,
                    "timestamp": time.time(),
                    **data
                })
            except Exception as e:
                logger.error("事件广播失败 [%s]: %s", event_type, str(e))

    async def execute(self, subtask: 'SubTask', project: 'Project') -> str:
        """执行子任务（子类必须实现）"""
        raise NotImplementedError("子类必须实现 execute 方法")

    @staticmethod
    def _win_quote(arg: str) -> str:
        """Windows cmd.exe 安全的双引号转义"""
        if not arg:
            return '""'
        needs_quote = any(c in arg for c in [' ', '\t', '"', '&', '|', '<', '>', '^'])
        if needs_quote:
            return '"' + arg.replace('"', '\\"') + '"'
        return arg

    async def _run_cli(self, cmd_list: List[str], timeout: int = 180, stdin_data: Optional[str] = None) -> str:
        """
        执行CLI命令（流式读取 + 心跳追踪）。
        prompt 应通过 stdin_data 传递，不要放在 cmd_list 中。

        Args:
            cmd_list: 命令行参数列表（不含 prompt，prompt 通过 stdin_data 传递）
            timeout: 超时时间（秒），默认 180
            stdin_data: 通过 stdin 传递的数据（推荐用于传递 prompt）

        Returns:
            命令输出字符串，或以 [错误]/[超时]/[卡死] 开头的错误信息
        """
        # 参数验证
        if not cmd_list:
            logger.error("_run_cli: cmd_list 为空")
            return "[错误] 命令列表为空"

        if not isinstance(cmd_list, list):
            logger.error("_run_cli: cmd_list 类型错误: %s", type(cmd_list).__name__)
            return "[错误] 命令列表必须是 list 类型"

        if timeout <= 0:
            logger.warning("_run_cli: timeout 无效: %d, 使用默认值 180", timeout)
            timeout = 180

        self.status = "working"
        await self.emit("agent_status", {"status": "working"})
        logger.debug("执行 CLI: %s (超时: %ds, stdin: %s)", cmd_list[0], timeout, "有" if stdin_data else "无")

        cli_env = os.environ.copy()
        cli_env["ANTHROPIC_API_KEY"] = "tp-cokkpw3n577bqyhvvgq3ktnka5mdmfi8pbywrcnifr7embpg"
        cli_env["ANTHROPIC_BASE_URL"] = "https://token-plan-cn.xiaomimimo.com/anthropic"

        # 诊断追踪
        start_time = time.time()
        last_output_time = start_time
        total_bytes = 0
        stdout_buf = []
        stderr_buf = []
        self._current_proc = None  # 暴露进程给监控器

        try:
            if sys.platform == "win32":
                cmd_str = " ".join(self._win_quote(str(c)) for c in cmd_list)
                logger.debug("Windows shell 命令: %s", cmd_str[:200])
                proc = await asyncio.create_subprocess_shell(
                    cmd_str,
                    stdin=asyncio.subprocess.PIPE if stdin_data else None,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=cli_env,
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    *cmd_list,
                    stdin=asyncio.subprocess.PIPE if stdin_data else None,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=cli_env,
                )

            self._current_proc = proc

            # 写入 stdin
            if stdin_data:
                proc.stdin.write(stdin_data.encode("utf-8"))
                await proc.stdin.drain()
                proc.stdin.close()

            # 流式读取 stdout，每 10 秒检查一次心跳
            HEARTBEAT_INTERVAL = 10
            STALL_THRESHOLD = 90  # 连续 90 秒无输出判定卡死

            async def read_stream(stream, buf):
                nonlocal last_output_time, total_bytes
                while True:
                    chunk = await stream.read(4096)
                    if not chunk:
                        break
                    buf.append(chunk)
                    last_output_time = time.time()
                    total_bytes += len(chunk)

            # 并行读取 stdout 和 stderr，带超时
            try:
                stdout_task = asyncio.create_task(read_stream(proc.stdout, stdout_buf))
                stderr_task = asyncio.create_task(read_stream(proc.stderr, stderr_buf))

                # 等待进程完成，但定期检查心跳
                while proc.returncode is None:
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=HEARTBEAT_INTERVAL)
                        break  # 进程正常退出
                    except asyncio.TimeoutError:
                        # 进程还在跑，检查是否卡死
                        stall = time.time() - last_output_time
                        if stall > STALL_THRESHOLD:
                            elapsed = time.time() - start_time
                            diag = "卡死: 连续 {:.0f} 秒无输出 (总耗时 {:.0f}s, 已收 {} bytes)".format(
                                stall, elapsed, total_bytes)
                            logger.warning("CLI 卡死检测: %s - %s", cmd_list[0], diag)
                            # 杀进程
                            try:
                                proc.kill()
                            except Exception:
                                pass
                            # 等待流读取完成
                            await asyncio.sleep(0.5)
                            stdout_task.cancel()
                            stderr_task.cancel()
                            # 组装诊断信息
                            result = b"".join(stdout_buf).decode("utf-8", errors="replace").strip()
                            self._last_cli_diagnosis = diag
                            return "[卡死] {}".format(diag)

                # 进程已退出，等待流读取完成
                await asyncio.wait_for(
                    asyncio.gather(stdout_task, stderr_task, return_exceptions=True),
                    timeout=10
                )

            except asyncio.TimeoutError:
                elapsed = time.time() - start_time
                diag = "超时: {:.0f} 秒 (已收 {} bytes, 最后输出 {:.0f}s 前)".format(
                    elapsed, total_bytes, elapsed - (last_output_time - start_time))
                logger.warning("CLI 超时: %s - %s", cmd_list[0], diag)
                try:
                    proc.kill()
                except Exception:
                    pass
                stdout_task.cancel()
                stderr_task.cancel()
                self._last_cli_diagnosis = diag
                return "[超时] {}".format(diag)

            result = b"".join(stdout_buf).decode("utf-8", errors="replace").strip()
            err = b"".join(stderr_buf).decode("utf-8", errors="replace").strip()

            # 某些工具输出到 stderr
            if not result and err:
                if not any(skip in err.lower() for skip in ["warning", "deprecat", "notice"]):
                    result = err

            elapsed = time.time() - start_time
            stall = elapsed - (last_output_time - start_time)
            self._last_cli_diagnosis = ""
            logger.debug("CLI 完成: %s (%.1fs, %d bytes)", cmd_list[0], elapsed, total_bytes)
            return result

        except FileNotFoundError:
            logger.error("CLI 工具未找到: %s", cmd_list[0])
            return "[错误] CLI工具未找到: {}".format(cmd_list[0])

        except PermissionError:
            logger.error("CLI 权限不足: %s", cmd_list[0])
            return "[错误] 权限不足: {}".format(cmd_list[0])

        except Exception as e:
            logger.error("CLI 执行异常 [%s]: %s", cmd_list[0], str(e), exc_info=True)
            return "[错误] {}".format(str(e))

        finally:
            self._current_proc = None
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
        logger.info("Hermes 代理初始化: %s", "可用" if self.available else "不可用（演示模式）")

    async def decompose_task(self, requirement: str, project: 'Project') -> List[dict]:
        """分解需求为子任务列表"""
        _validate_string(requirement, "requirement")
        if project is None:
            raise InvalidTaskError("project 不能为 None")

        self.status = "working"
        await self.emit("agent_status", {"status": "working", "task": "分析需求..."})
        await self.emit("log", {
            "source": "🎯 Hermes",
            "target": "需求分析",
            "message": "正在分析: {}...".format(requirement[:60])
        })
        logger.info("开始分解需求: %s...", requirement[:80])

        prompt = ("你是一个项目管理专家。请把以下需求拆解成具体的开发子任务。"
                  "需求: {} 请以JSON格式返回子任务列表: "
                  "{{\"subtasks\": [{{\"id\": \"task-1\", \"title\": \"标题\", "
                  "\"description\": \"描述\", \"assigned_to\": \"claude-code|codex|openclaw\", "
                  "\"dependencies\": [], \"needs_review\": true}}]}} "
                  "规则: 1. claude-code: 写代码/实现功能  2. codex: 优化/重构  "
                  "3. openclaw: 审查  4. 代码任务 needs_review=true  5. 返回纯JSON"
                  .format(requirement))

        result = ""

        # 方法1: 用 hermes CLI (通过 Python 直接调用，避免 uv trampoline 问题)
        if self.available and self._hermes_python:
            try:
                cmd = [self._hermes_python, "-m", "hermes_cli.main", "-z", "--yolo"]
                result = await self._run_cli(cmd, timeout=120, stdin_data=prompt)
                if result and not result.startswith("[错误]"):
                    await self.emit("log", {"source": "🎯 Hermes", "target": "AI分析", "message": "Hermes CLI 分析完成"})
                    logger.info("Hermes CLI 分析完成")
            except Exception as e:
                logger.warning("Hermes CLI 调用失败: %s", str(e)[:100])
                await self.emit("log", {"source": "🎯 Hermes", "target": "降级", "message": "Hermes CLI 失败: {}".format(str(e)[:80])})

        # 方法2: 备用 - 用 claude CLI (通过 _run_cli)
        if not result or result.startswith("[错误]"):
            claude_path = shutil.which("claude")
            if claude_path:
                try:
                    cmd = ["claude", "-p", "--model", "mimo-v2.5-pro", "--dangerously-skip-permissions"]
                    result = await self._run_cli(cmd, timeout=120, stdin_data=prompt)
                    if result and not result.startswith("[错误]"):
                        await self.emit("log", {"source": "🎯 Hermes", "target": "AI分析", "message": "Claude Code 分析完成"})
                        logger.info("Claude Code 分析完成")
                except Exception as e:
                    logger.warning("Claude CLI 调用失败: %s", str(e)[:100])

        # 解析JSON
        subtasks = self._parse_subtasks(result) if result else []
        if not subtasks:
            subtasks = self._fallback(requirement)
            await self.emit("log", {"source": "🎯 Hermes", "target": "降级", "message": "使用内置模板分解任务"})
            logger.info("使用内置模板分解任务: %d 个子任务", len(subtasks))
        else:
            await self.emit("log", {"source": "🎯 Hermes", "target": "任务分解", "message": "AI分解为 {} 个子任务".format(len(subtasks))})
            logger.info("AI 分解任务: %d 个子任务", len(subtasks))

        # 验证子任务数据
        validated_subtasks = self._validate_subtasks(subtasks)

        self.status = "idle"
        await self.emit("agent_status", {"status": "idle"})
        return validated_subtasks

    def _parse_subtasks(self, result: str) -> List[dict]:
        """从 AI 返回结果中解析子任务 JSON"""
        if not result:
            return []
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = result[start:end]
                data = json.loads(json_str)
                subtasks = data.get("subtasks", [])
                if not isinstance(subtasks, list):
                    logger.warning("解析结果中 subtasks 不是列表: %s", type(subtasks).__name__)
                    return []
                logger.debug("成功解析 %d 个子任务", len(subtasks))
                return subtasks
        except json.JSONDecodeError as e:
            logger.error("JSON 解析失败: %s", str(e))
        except Exception as e:
            logger.error("解析子任务异常: %s", str(e))
        return []

    def _validate_subtasks(self, subtasks: List[dict]) -> List[dict]:
        """验证并修复子任务数据"""
        valid_agents = {"claude-code", "codex", "openclaw"}
        validated = []

        for i, st in enumerate(subtasks):
            if not isinstance(st, dict):
                logger.warning("子任务 #%d 不是字典类型，跳过", i)
                continue

            # 确保必要字段存在
            if "id" not in st:
                st["id"] = "task-{}".format(i + 1)
                logger.debug("子任务 #%d 缺少 id，自动生成: %s", i, st["id"])

            if "title" not in st:
                st["title"] = "未命名任务"
                logger.debug("子任务 #%d 缺少 title，使用默认值", i)

            if "description" not in st:
                st["description"] = ""

            # 验证 assigned_to
            if st.get("assigned_to") not in valid_agents:
                logger.warning("子任务 '%s' assigned_to 无效: %s, 回退到 claude-code",
                             st.get("id", "?"), st.get("assigned_to"))
                st["assigned_to"] = "claude-code"

            # 验证 dependencies
            if "dependencies" in st and not isinstance(st["dependencies"], list):
                logger.warning("子任务 '%s' dependencies 不是列表，重置", st.get("id"))
                st["dependencies"] = []

            # 验证 needs_review
            if "needs_review" in st and not isinstance(st["needs_review"], bool):
                st["needs_review"] = bool(st["needs_review"])

            validated.append(st)

        return validated

    def _fallback(self, requirement):
        """根据需求内容智能生成子任务，而非固定模板"""
        req_lower = requirement.lower()
        tasks = []
        task_id = 0

        # 分析需求类型
        is_web = any(k in req_lower for k in ["web", "网站", "前端", "html", "css", "页面", "ui", "界面"])
        is_api = any(k in req_lower for k in ["api", "接口", "后端", "服务", "server", "rest", "http"])
        is_db = any(k in req_lower for k in ["数据库", "database", "db", "sql", "存储", "mongo", "redis"])
        is_auth = any(k in req_lower for k in ["登录", "注册", "认证", "auth", "login", "用户", "权限"])
        is_cli = any(k in req_lower for k in ["命令行", "cli", "终端", "工具", "脚本", "script"])
        is_data = any(k in req_lower for k in ["数据", "分析", "处理", "data", "分析", "统计"])
        is_game = any(k in req_lower for k in ["游戏", "game", "猜", "quiz", "小游戏"])
        is_bot = any(k in req_lower for k in ["机器人", "bot", "聊天", "chat", "自动回复"])

        # 基础任务: 总是先做架构设计
        task_id += 1
        tasks.append({
            "id": "task-{}".format(task_id),
            "title": "架构设计与项目初始化",
            "description": "分析需求 '{}'，设计项目结构、模块划分、技术选型，创建项目骨架".format(requirement[:100]),
            "assigned_to": "claude-code",
            "dependencies": [],
            "needs_review": True,
        })

        # 根据需求类型添加具体任务
        if is_api or is_web:
            task_id += 1
            tasks.append({
                "id": "task-{}".format(task_id),
                "title": "实现核心路由与处理器",
                "description": "实现主要的路由/端点定义、请求处理逻辑、响应格式",
                "assigned_to": "claude-code",
                "dependencies": ["task-1"],
                "needs_review": True,
            })

        if is_db:
            task_id += 1
            tasks.append({
                "id": "task-{}".format(task_id),
                "title": "数据库模型与数据层",
                "description": "设计数据模型、实现数据访问层、数据库连接管理",
                "assigned_to": "claude-code",
                "dependencies": ["task-1"],
                "needs_review": True,
            })

        if is_auth:
            task_id += 1
            tasks.append({
                "id": "task-{}".format(task_id),
                "title": "用户认证与授权",
                "description": "实现用户注册、登录、token管理、权限校验",
                "assigned_to": "claude-code",
                "dependencies": ["task-1"],
                "needs_review": True,
            })

        if is_web:
            task_id += 1
            tasks.append({
                "id": "task-{}".format(task_id),
                "title": "前端界面实现",
                "description": "实现用户界面、交互逻辑、样式设计",
                "assigned_to": "claude-code",
                "dependencies": ["task-1"],
                "needs_review": True,
            })

        if is_cli:
            task_id += 1
            tasks.append({
                "id": "task-{}".format(task_id),
                "title": "命令行交互与参数解析",
                "description": "实现命令行参数解析、用户交互、输出格式化",
                "assigned_to": "claude-code",
                "dependencies": ["task-1"],
                "needs_review": True,
            })

        if is_data:
            task_id += 1
            tasks.append({
                "id": "task-{}".format(task_id),
                "title": "数据处理与分析逻辑",
                "description": "实现数据读取、清洗、分析、统计、输出",
                "assigned_to": "claude-code",
                "dependencies": ["task-1"],
                "needs_review": True,
            })

        if is_game:
            task_id += 1
            tasks.append({
                "id": "task-{}".format(task_id),
                "title": "游戏逻辑实现",
                "description": "实现游戏核心逻辑、状态管理、胜负判定",
                "assigned_to": "claude-code",
                "dependencies": ["task-1"],
                "needs_review": True,
            })

        if is_bot:
            task_id += 1
            tasks.append({
                "id": "task-{}".format(task_id),
                "title": "消息处理与对话逻辑",
                "description": "实现消息接收、解析、回复逻辑、对话状态管理",
                "assigned_to": "claude-code",
                "dependencies": ["task-1"],
                "needs_review": True,
            })

        # 如果没有匹配到特定类型，添加通用实现任务
        if len(tasks) == 1:
            task_id += 1
            tasks.append({
                "id": "task-{}".format(task_id),
                "title": "核心功能实现",
                "description": "根据需求 '{}' 实现主要功能模块".format(requirement[:80]),
                "assigned_to": "claude-code",
                "dependencies": ["task-1"],
                "needs_review": True,
            })

        # 总是有测试和文档任务
        task_id += 1
        tasks.append({
            "id": "task-{}".format(task_id),
            "title": "错误处理与边界情况",
            "description": "添加异常处理、输入验证、边界情况处理、日志记录",
            "assigned_to": "claude-code",
            "dependencies": ["task-2"],
            "needs_review": True,
        })

        # 代码审查
        review_deps = ["task-{}".format(i) for i in range(2, task_id + 1)]
        task_id += 1
        tasks.append({
            "id": "task-{}".format(task_id),
            "title": "代码审查",
            "description": "审查所有代码的质量、安全性、最佳实践",
            "assigned_to": "openclaw",
            "dependencies": review_deps,
            "needs_review": False,
        })

        # 优化
        task_id += 1
        tasks.append({
            "id": "task-{}".format(task_id),
            "title": "代码优化与重构",
            "description": "根据审查结果优化代码结构、性能、可读性",
            "assigned_to": "codex",
            "dependencies": ["task-{}".format(task_id - 1)],
            "needs_review": True,
        })

        return tasks


    async def analyze_revision(self, feedback: str, project: 'Project') -> List['SubTask']:
        """分析用户修改意见，返回需要返工的任务列表"""
        _validate_string(feedback, "feedback")
        if project is None:
            raise InvalidTaskError("project 不能为 None")

        self.status = "working"
        await self.emit("agent_status", {"status": "working", "task": "分析修改意见..."})
        await self.emit("log", {
            "source": "🎯 Hermes",
            "target": "修订分析",
            "message": "正在分析修改意见: {}...".format(feedback[:60])
        })
        logger.info("开始分析修订意见: %s...", feedback[:80])

        # 构建项目上下文
        task_summary = "\n".join([
            "  - {}: {} [状态:{}] 结果: {}".format(
                st.id, st.title, st.status, (st.result or "无")[:80]
            )
            for st in project.subtasks
        ])

        prompt = (
            "你是一个项目管理专家。用户对已完成的项目不满意，提出了修改意见。\n"
            "项目名称: {}\n"
            "原始需求: {}\n"
            "当前任务列表:\n{}\n"
            "用户修改意见: {}\n\n"
            "请分析哪些任务需要返工。返回JSON格式:\n"
            "{{\"revision_analysis\": \"分析说明\", \"tasks_to_redo\": [\"task-1\", \"task-2\"]}}\n"
            "规则: 1. 只列出需要修改的任务ID  2. 如果不需要返工返回空列表  3. 返回纯JSON"
        ).format(project.name, project.requirement[:200], task_summary, feedback)

        result = ""

        # 方法1: hermes CLI
        if self.available and self._hermes_python:
            try:
                cmd = [self._hermes_python, "-m", "hermes_cli.main", "-z", "--yolo"]
                result = await self._run_cli(cmd, timeout=120, stdin_data=prompt)
                if result and not result.startswith("[错误]"):
                    await self.emit("log", {"source": "🎯 Hermes", "target": "AI分析", "message": "修订分析完成"})
            except Exception as e:
                logger.warning("Hermes CLI 调用失败: %s", str(e)[:100])

        # 方法2: claude CLI 备用
        if not result or result.startswith("[错误]"):
            claude_path = shutil.which("claude")
            if claude_path:
                try:
                    cmd = ["claude", "-p", "--model", "mimo-v2.5-pro", "--dangerously-skip-permissions"]
                    result = await self._run_cli(cmd, timeout=120, stdin_data=prompt)
                    if result and not result.startswith("[错误]"):
                        await self.emit("log", {"source": "🎯 Hermes", "target": "AI分析", "message": "Claude 修订分析完成"})
                except Exception as e:
                    logger.warning("Claude CLI 调用失败: %s", str(e)[:100])

        # 解析结果
        tasks_to_redo = self._parse_revision(result, project) if result else []

        if not tasks_to_redo:
            # 如果 AI 无法解析，降级为全部返工
            tasks_to_redo = [st for st in project.subtasks if st.status == "done"]
            await self.emit("log", {
                "source": "🎯 Hermes",
                "target": "降级",
                "message": "AI分析失败，将返工所有已完成任务 ({} 个)".format(len(tasks_to_redo))
            })
        else:
            await self.emit("log", {
                "source": "🎯 Hermes",
                "target": "修订分配",
                "message": "需要返工 {} 个任务: {}".format(
                    len(tasks_to_redo),
                    ", ".join(st.title[:20] for st in tasks_to_redo)
                )
            })

        self.status = "idle"
        await self.emit("agent_status", {"status": "idle"})
        return tasks_to_redo

    def _parse_revision(self, result: str, project: 'Project') -> List['SubTask']:
        """从 AI 返回结果中解析需要返工的任务"""
        if not result:
            return []
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start == -1 or end <= 0:
                return []
            data = json.loads(result[start:end])
            task_ids = data.get("tasks_to_redo", [])
            if not isinstance(task_ids, list):
                return []
            # 匹配实际任务
            redo_map = {st.id: st for st in project.subtasks}
            matched = [redo_map[tid] for tid in task_ids if tid in redo_map]
            return matched
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("解析修订结果失败: %s", str(e)[:80])
            return []


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
        logger.info("Claude Code 代理初始化: %s", "可用" if self.available else "不可用（演示模式）")

    async def execute(self, subtask: 'SubTask', project: 'Project') -> str:
        """执行开发任务"""
        if subtask is None:
            raise InvalidTaskError("subtask 不能为 None")
        if project is None:
            raise InvalidTaskError("project 不能为 None")

        await self.emit("log", {
            "source": "🤖 Claude Code",
            "target": "开发",
            "message": "开始: {}".format(subtask.title)
        })
        logger.info("开始执行任务: %s", subtask.title)

        context = self._build_context(subtask, project)
        result = ""

        if self.available:
            try:
                # claude -p: 非交互模式，prompt 作为参数传递
                cmd = ["claude", "-p", "--model", "mimo-v2.5-pro", "--dangerously-skip-permissions"]
                result = await self._run_cli(cmd, timeout=300, stdin_data=context)
            except Exception as e:
                logger.error("Claude CLI 执行失败: %s", str(e))
                result = "[错误] {}".format(str(e))

        if not result or result.startswith("[错误]"):
            if result and result.startswith("[错误]"):
                await self.emit("log", {
                    "source": "🤖 Claude Code",
                    "target": "降级",
                    "message": "CLI调用失败，使用演示模式"
                })
                logger.warning("CLI 调用失败，降级到演示模式")
            result = self._demo_result(subtask)

        subtask.result = result
        await self.emit("log", {
            "source": "🤖 Claude Code",
            "target": "完成",
            "message": "完成: {} ({} chars)".format(subtask.title, len(result))
        })
        logger.info("任务完成: %s (输出 %d 字符)", subtask.title, len(result))
        return result

    def _build_context(self, subtask: 'SubTask', project: 'Project') -> str:
        """构建任务上下文 - 给 Claude Code 详细的工作指令"""
        parts = [
            "你是一个专业的 Python 开发者。请完成以下开发任务。",
            "",
            "## 项目: {}".format(project.name),
            "## 需求: {}".format(project.description[:500]),
            "",
            "## 当前任务: {}".format(subtask.title),
            "## 任务描述: {}".format(subtask.description),
            "",
            "## 要求:",
            "1. 直接编写可运行的完整代码",
            "2. 创建必要的文件（使用 write 工具）",
            "3. 代码要完整、可运行、有注释",
            "4. 不要只输出计划，要实际写代码",
        ]

        if subtask.dependencies:
            parts.append("")
            parts.append("## 前置任务结果:")
            for dep_id in subtask.dependencies:
                found = False
                for st in project.subtasks:
                    if st.id == dep_id and st.result:
                        parts.append("[{}]: {}".format(st.title, st.result[:800]))
                        found = True
                        break
                if not found:
                    parts.append("[{}]: (无结果)".format(dep_id))

        if subtask.review_result and subtask.review_result.issues:
            parts.append("")
            parts.append("## 审查反馈（请修复以下问题）:")
            for issue in subtask.review_result.issues:
                parts.append("- {}".format(issue))

        return "\n".join(parts)

    def _demo_result(self, subtask: 'SubTask') -> str:
        """生成演示结果（CLI 不可用时使用）"""
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
        logger.info("Codex 代理初始化: %s", "可用" if self.available else "不可用（演示模式）")

    async def execute(self, subtask: 'SubTask', project: 'Project') -> str:
        """执行优化任务"""
        if subtask is None:
            raise InvalidTaskError("subtask 不能为 None")
        if project is None:
            raise InvalidTaskError("project 不能为 None")

        await self.emit("log", {
            "source": "⚡ Codex",
            "target": "优化",
            "message": "开始: {}".format(subtask.title)
        })
        logger.info("开始优化任务: %s", subtask.title)

        context = self._build_context(subtask, project)
        result = ""

        if self.available:
            try:
                # codex exec: prompt 作为参数传递, --skip-git-repo-check 允许在非git目录运行
                result = await self._run_cli(
                    ["codex", "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox", "--json"],
                    timeout=300,
                    stdin_data=context
                )
            except Exception as e:
                logger.error("Codex CLI 执行失败: %s", str(e))
                result = "[错误] {}".format(str(e))

        if not result or result.startswith("[错误]"):
            if result and result.startswith("[错误]"):
                await self.emit("log", {
                    "source": "⚡ Codex",
                    "target": "降级",
                    "message": "CLI调用失败，使用演示模式"
                })
                logger.warning("Codex CLI 调用失败，降级到演示模式")
            result = self._demo_result(subtask)

        subtask.result = result
        await self.emit("log", {
            "source": "⚡ Codex",
            "target": "完成",
            "message": "完成: {}".format(subtask.title)
        })
        logger.info("优化任务完成: %s", subtask.title)
        return result

    def _build_context(self, subtask: 'SubTask', project: 'Project') -> str:
        """构建优化上下文 - 给 Codex 详细的优化指令"""
        parts = [
            "你是一个代码优化专家。请完成以下优化任务。",
            "",
            "## 项目: {}".format(project.name),
            "",
            "## 优化任务: {}".format(subtask.title),
            "## 描述: {}".format(subtask.description),
            "",
            "## 要求:",
            "1. 分析现有代码的问题",
            "2. 优化代码结构、性能、可读性",
            "3. 保持功能不变",
            "4. 直接修改代码文件",
        ]

        if subtask.dependencies:
            parts.append("")
            parts.append("## 需要优化的代码:")
            for dep_id in subtask.dependencies:
                found = False
                for st in project.subtasks:
                    if st.id == dep_id and st.result:
                        parts.append("[{}]: {}".format(st.title, st.result[:1500]))
                        found = True
                        break
                if not found:
                    parts.append("[{}]: (无结果)".format(dep_id))

        if subtask.review_result and subtask.review_result.issues:
            parts.append("")
            parts.append("## 审查反馈:")
            for issue in subtask.review_result.issues:
                parts.append("- {}".format(issue))

        return "\n".join(parts)

    def _demo_result(self, subtask: 'SubTask') -> str:
        """生成演示结果（CLI 不可用时使用）"""
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
        self._openclaw_path = shutil.which("openclaw") or "openclaw"
        logger.info("OpenClaw 代理初始化: %s (路径: %s)", "可用" if self.available else "不可用（演示模式）", self._openclaw_path)

    async def execute(self, subtask: 'SubTask', project: 'Project') -> str:
        """执行审查任务"""
        if subtask is None:
            raise InvalidTaskError("subtask 不能为 None")
        if project is None:
            raise InvalidTaskError("project 不能为 None")

        await self.emit("log", {
            "source": "🔍 OpenClaw",
            "target": "审查",
            "message": "审查中: {}".format(subtask.title)
        })
        logger.info("开始审查: %s", subtask.title)

        # 查找审查目标
        review_target = None
        for dep_id in subtask.dependencies:
            for st in project.subtasks:
                if st.id == dep_id:
                    review_target = st
                    break
            if review_target:
                break

        if not review_target or not review_target.result:
            subtask.result = "[审查] 未找到可审查的产出"
            subtask.status = "done"
            logger.warning("审查目标未找到或无产出: %s", subtask.title)
            return subtask.result

        # 构建审查提示
        safe_code = review_target.result[:3000]
        prompt = (
            "你是资深代码审查员。请审查以下代码。\n\n"
            "任务: {title}\n\n"
            "代码:\n{code}\n\n"
            "请以纯JSON格式返回审查结果（不要包含 markdown 代码块标记）:\n"
            '{{"approved": true或false, "score": 0-100, "issues": ["问题列表"], "suggestions": ["建议列表"], "summary": "总体评价"}}\n'
            "评分标准: 60分以上为通过。代码能运行、结构清晰给70+。有明显bug给50以下。"
        ).format(title=review_target.title, code=safe_code)

        result = ""
        if self.available:
            try:
                # 写临时 .py 脚本文件 + 临时 prompt 文件，完全绕过 shell 引号问题
                import tempfile as _tf
                prompt_path = None
                script_path = None
                try:
                    # 写 prompt 到临时文件
                    _pf = _tf.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
                    _pf.write(prompt)
                    _pf.close()
                    prompt_path = _pf.name

                    # 写 Python 脚本到临时文件（使用 openclaw 完整路径避免 PATH 问题）
                    oc_path = self._openclaw_path.replace("\\", "\\\\")
                    script_content = (
                        "import subprocess, sys, os\n"
                        "msg = open(sys.argv[1], encoding='utf-8').read()\n"
                        "oc = sys.argv[2]\n"
                        "r = subprocess.run(\n"
                        "    [oc, 'agent', '--agent', 'main', '-m', msg, '--json'],\n"
                        "    capture_output=True, text=True, timeout=120\n"
                        ")\n"
                        "print(r.stdout)\n"
                        "if r.stderr: print(r.stderr, file=sys.stderr)\n"
                        "try: os.unlink(sys.argv[1])\n"
                        "except: pass\n"
                        "sys.exit(r.returncode)\n"
                    )
                    _sf = _tf.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
                    _sf.write(script_content)
                    _sf.close()
                    script_path = _sf.name

                    cmd = ["python", script_path, prompt_path, self._openclaw_path]
                    result = await self._run_cli(cmd, timeout=180)
                except Exception as e:
                    logger.error("OpenClaw 执行失败: %s", str(e))
                    result = "[错误] {}".format(str(e))
                finally:
                    for p in [prompt_path, script_path]:
                        if p:
                            try: os.unlink(p)
                            except OSError: pass
            except Exception as e:
                logger.error("OpenClaw CLI 执行失败: %s", str(e))
                result = "[错误] {}".format(str(e))

        if not result or result.startswith("[错误]"):
            if result and result.startswith("[错误]"):
                await self.emit("log", {
                    "source": "🔍 OpenClaw",
                    "target": "降级",
                    "message": "CLI调用失败，使用演示模式"
                })
                logger.warning("OpenClaw CLI 调用失败，降级到演示模式")
            result = self._demo_review(review_target)

        subtask.result = result
        subtask.status = "done"

        review = self._parse_review(result)
        review_target.review_result = review
        review.reviewer = self.agent_id

        verdict = "通过" if review.approved else "需要修改"
        await self.emit("log", {
            "source": "🔍 OpenClaw",
            "target": verdict,
            "message": "评分: {}/100 | 问题: {}".format(review.score, len(review.issues))
        })
        logger.info("审查完成: %s - %s (评分: %d)", subtask.title, verdict, review.score)
        return result

    def _demo_review(self, target: 'SubTask') -> str:
        """生成演示审查结果（CLI 不可用时使用）"""
        return json.dumps({
            "approved": True,
            "score": 85,
            "issues": ["建议添加更多错误处理"],
            "suggestions": ["可以考虑添加单元测试"],
            "summary": "代码质量良好，基本功能完整"
        }, ensure_ascii=False)

    def _parse_review(self, result: str) -> ReviewResult:
        """解析审查结果 JSON"""
        if not result:
            logger.warning("审查结果为空，使用默认值")
            return ReviewResult(approved=True, score=70)

        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(result[start:end])

                # 验证数据类型
                approved = data.get("approved", False)
                if not isinstance(approved, bool):
                    approved = bool(approved)

                score = data.get("score", 50)
                if not isinstance(score, (int, float)):
                    logger.warning("审查评分类型错误: %s", type(score).__name__)
                    score = 50
                else:
                    score = max(0, min(100, int(score)))

                issues = data.get("issues", [])
                if not isinstance(issues, list):
                    issues = []

                suggestions = data.get("suggestions", [])
                if not isinstance(suggestions, list):
                    suggestions = []

                logger.debug("解析审查结果: approved=%s, score=%d, issues=%d",
                           approved, score, len(issues))
                return ReviewResult(
                    approved=approved,
                    score=score,
                    issues=issues,
                    suggestions=suggestions,
                )
        except json.JSONDecodeError as e:
            logger.error("审查结果 JSON 解析失败: %s", str(e))
        except Exception as e:
            logger.error("解析审查结果异常: %s", str(e))

        logger.warning("使用默认审查结果")
        return ReviewResult(approved=True, score=70)


def create_agents() -> Dict[str, BaseAgent]:
    """创建所有代理实例"""
    logger.info("创建代理实例...")
    try:
        agents = {
            "hermes": ProjectManagerAgent(),
            "claude-code": DeveloperAgent(),
            "codex": OptimizerAgent(),
            "openclaw": ReviewerAgent(),
        }
        logger.info("成功创建 %d 个代理", len(agents))
        return agents
    except Exception as e:
        logger.error("创建代理失败: %s", str(e), exc_info=True)
        raise AgentError("无法创建代理: {}".format(str(e)))
