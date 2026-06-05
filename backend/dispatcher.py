"""
AI工作室 - 任务调度器
管理项目生命周期: 需求分解 -> 任务分配 -> 执行 -> 审查 -> 修订 -> 完成
"""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Set
from agents import (
    BaseAgent, Project, SubTask, ReviewResult, create_agents,
    InvalidTaskError, AgentNotAvailableError, AgentError
)

# 模块级日志记录器
logger = logging.getLogger(__name__)


@dataclass
class TimeoutDiagnosis:
    """超时诊断结果"""
    reason: str  # stuck | slow | deadlock | network | unknown
    task_id: str = ""
    task_title: str = ""
    agent_id: str = ""
    elapsed: float = 0.0
    last_activity: float = 0.0
    stall_seconds: float = 0.0
    bytes_received: int = 0
    cli_diagnosis: str = ""
    suggestion: str = ""  # 建议动作: retry | split | skip | abort

    def to_dict(self) -> dict:
        return {
            "reason": self.reason,
            "task_id": self.task_id,
            "task_title": self.task_title,
            "agent_id": self.agent_id,
            "elapsed": round(self.elapsed, 1),
            "stall_seconds": round(self.stall_seconds, 1),
            "bytes_received": self.bytes_received,
            "cli_diagnosis": self.cli_diagnosis,
            "suggestion": self.suggestion,
        }

# 项目执行全局超时 (秒)
PROJECT_EXECUTION_TIMEOUT = 600


# ──────────────────────────────────────────────
# 自定义异常
# ──────────────────────────────────────────────

class DispatcherError(Exception):
    """调度器错误基类"""
    pass


class CircularDependencyError(DispatcherError):
    """循环依赖错误"""
    pass


class MissingDependencyError(DispatcherError):
    """缺失依赖错误"""
    pass


class ProjectNotFoundError(DispatcherError):
    """项目未找到错误"""
    pass


class ProjectTimeoutError(DispatcherError):
    """项目执行超时"""
    pass


# ──────────────────────────────────────────────
# 输入验证函数
# ──────────────────────────────────────────────

def _validate_project_name(name: str) -> None:
    """验证项目名称"""
    if not isinstance(name, str):
        raise InvalidTaskError("项目名称必须是字符串")
    if not name.strip():
        raise InvalidTaskError("项目名称不能为空")


def _validate_requirement(requirement: str) -> None:
    """验证需求描述"""
    if not isinstance(requirement, str):
        raise InvalidTaskError("需求描述必须是字符串")
    if not requirement.strip():
        raise InvalidTaskError("需求描述不能为空")


def _detect_circular_dependencies(subtasks: List[SubTask]) -> Optional[List[str]]:
    """
    检测子任务中的循环依赖

    Returns:
        None 如果无循环依赖，否则返回循环路径
    """
    # 构建依赖图
    graph: Dict[str, List[str]] = {}
    for st in subtasks:
        graph[st.id] = st.dependencies

    visited: Set[str] = set()
    rec_stack: Set[str] = set()
    path: List[str] = []

    def dfs(node: str) -> Optional[List[str]]:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for dep in graph.get(node, []):
            if dep not in visited:
                result = dfs(dep)
                if result:
                    return result
            elif dep in rec_stack:
                # 找到循环
                cycle_start = path.index(dep)
                return path[cycle_start:] + [dep]

        path.pop()
        rec_stack.discard(node)
        return None

    for node in graph:
        if node not in visited:
            result = dfs(node)
            if result:
                return result

    return None


def _validate_task_dependencies(subtasks: List[SubTask]) -> List[str]:
    """
    验证任务依赖的有效性

    Returns:
        警告信息列表
    """
    warnings = []
    task_ids = {st.id for st in subtasks}

    for st in subtasks:
        for dep_id in st.dependencies:
            if dep_id not in task_ids:
                warnings.append("任务 '{}' 依赖 '{}' 但该任务不存在".format(st.id, dep_id))
            elif dep_id == st.id:
                warnings.append("任务 '{}' 依赖自己".format(st.id))

    return warnings


class StudioDispatcher:
    """任务调度器 - 管理项目生命周期"""

    def __init__(self, agents: Dict[str, BaseAgent]):
        if not isinstance(agents, dict):
            raise TypeError("agents 必须是字典类型")
        if not agents:
            logger.warning("agents 字典为空")

        self.agents = agents
        self.projects: Dict[str, Project] = {}
        self._broadcast: Optional[Callable] = None
        logger.info("调度器初始化: %d 个代理", len(agents))

    def set_broadcaster(self, broadcast_fn: Callable):
        """设置事件广播函数"""
        if broadcast_fn is None:
            logger.warning("set_broadcaster 接收到 None")
            return
        if not callable(broadcast_fn):
            raise TypeError("broadcaster 必须是可调用对象")

        self._broadcast = broadcast_fn
        for agent in self.agents.values():
            agent.set_broadcaster(broadcast_fn)
        logger.debug("广播函数已设置")

    async def broadcast(self, message: dict):
        """广播消息到所有客户端"""
        if not isinstance(message, dict):
            logger.warning("broadcast: message 不是字典: %s", type(message).__name__)
            return
        if self._broadcast:
            try:
                await self._broadcast(message)
            except Exception as e:
                logger.error("广播消息失败: %s", str(e))

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """按名称获取项目"""
        for proj in self.projects.values():
            if proj.name == name:
                return proj
        return None

    def get_project(self, project_id: str) -> Optional[Project]:
        """根据 ID 获取项目"""
        if not isinstance(project_id, str):
            logger.warning("get_project: project_id 类型错误: %s", type(project_id).__name__)
            return None
        return self.projects.get(project_id)

    async def start_project(self, name: str, requirement: str) -> Project:
        """
        启动新项目

        Args:
            name: 项目名称
            requirement: 需求描述

        Returns:
            完成的项目对象

        Raises:
            InvalidTaskError: 输入参数无效
            DispatcherError: 调度过程中的错误
        """
        _validate_project_name(name)
        _validate_requirement(requirement)

        project_id = "proj-{}".format(uuid.uuid4().hex[:8])
        project = Project(id=project_id, name=name, description=requirement)
        self.projects[project_id] = project

        logger.info("启动项目: %s (%s)", name, project_id)
        await self.broadcast({
            "type": "project_created",
            "project_id": project_id,
            "name": name,
            "requirement": requirement
        })

        try:
            # 阶段1: 需求分解
            await self.broadcast({
                "type": "phase_change",
                "phase": "planning",
                "message": "项目经理正在分析需求..."
            })
            project.status = "planning"

            pm = self.agents.get("hermes")
            if not pm:
                raise AgentNotAvailableError("项目经理代理不可用")

            subtask_dicts = await pm.decompose_task(requirement, project)

            # 创建子任务对象
            project.subtasks = []
            for st_dict in subtask_dicts:
                try:
                    st = SubTask(
                        id=st_dict.get("id", "task-{}".format(uuid.uuid4().hex[:6])),
                        title=st_dict.get("title", "未命名"),
                        description=st_dict.get("description", ""),
                        assigned_to=st_dict.get("assigned_to", "claude-code"),
                        dependencies=st_dict.get("dependencies", []),
                        needs_review=st_dict.get("needs_review", True),
                    )
                    project.subtasks.append(st)
                except Exception as e:
                    logger.warning("创建子任务失败: %s - %s", st_dict, str(e))

            # 验证依赖关系
            dep_warnings = _validate_task_dependencies(project.subtasks)
            for warning in dep_warnings:
                logger.warning("依赖警告: %s", warning)
                await self.broadcast({
                    "type": "log",
                    "source": "调度器",
                    "target": "警告",
                    "message": warning
                })

            # 检测循环依赖
            cycle = _detect_circular_dependencies(project.subtasks)
            if cycle:
                cycle_str = " -> ".join(cycle)
                logger.error("检测到循环依赖: %s", cycle_str)
                raise CircularDependencyError("检测到循环依赖: {}".format(cycle_str))

            await self.broadcast({
                "type": "task_breakdown",
                "project_id": project_id,
                "subtasks": [self._st_dict(st) for st in project.subtasks]
            })

            # 阶段2: 执行（带全局超时保护）
            project.status = "executing"
            await self.broadcast({
                "type": "phase_change",
                "phase": "executing",
                "message": "开始执行 {} 个子任务".format(len(project.subtasks))
            })
            try:
                await asyncio.wait_for(
                    self._execute_project_with_heartbeat(project),
                    timeout=PROJECT_EXECUTION_TIMEOUT
                )
            except asyncio.TimeoutError:
                # 收集诊断信息
                diagnosis = self._diagnose_timeout(project)
                logger.error("项目执行超时: %s - 原因: %s, 建议: %s",
                            name, diagnosis.reason, diagnosis.suggestion)
                # 将未完成的任务标记为失败
                for st in project.subtasks:
                    if st.status not in ("done", "failed"):
                        st.status = "failed"
                        st.error = "超时[{}]: {}".format(diagnosis.reason, diagnosis.suggestion)
                # 广播诊断结果
                await self.broadcast({
                    "type": "timeout_diagnosis",
                    "diagnosis": diagnosis.to_dict()
                })
                raise ProjectTimeoutError(
                    "项目 '{}' 执行超时: {}".format(name, diagnosis.suggestion)
                )

        except (CircularDependencyError, AgentNotAvailableError, ProjectTimeoutError) as e:
            project.status = "error"
            logger.error("项目执行失败: %s", str(e))
            await self.broadcast({
                "type": "phase_change",
                "phase": "error",
                "message": "项目执行出错: {}".format(str(e))
            })
            raise

        except Exception as e:
            project.status = "error"
            logger.error("项目执行异常: %s", str(e), exc_info=True)
            await self.broadcast({
                "type": "phase_change",
                "phase": "error",
                "message": "项目执行出错: {}".format(str(e)[:200])
            })
            raise DispatcherError("项目执行失败: {}".format(str(e)))

        # 阶段3: 完成
        project.status = "done"
        done_count = len([st for st in project.subtasks if st.status == "done"])
        fail_count = len([st for st in project.subtasks if st.status == "failed"])

        await self.broadcast({
            "type": "project_complete",
            "project_id": project_id,
            "success": fail_count == 0,
            "total_tasks": len(project.subtasks),
            "completed": done_count,
            "failed": fail_count
        })
        await self.broadcast({
            "type": "phase_change",
            "phase": "done",
            "message": "项目完成! {}/{} 任务成功".format(done_count, len(project.subtasks))
        })

        logger.info("项目完成: %s (成功: %d, 失败: %d)", name, done_count, fail_count)
        return project

    async def _execute_project(self, project: Project):
        """执行项目中的所有子任务"""
        max_rounds = 10
        consecutive_empty = 0  # 连续无就绪任务计数

        for round_num in range(1, max_rounds + 1):
            ready = self._get_ready(project)

            if not ready:
                pending = [st for st in project.subtasks if st.status not in ("done", "failed")]
                if not pending:
                    logger.info("所有任务已完成")
                    break

                consecutive_empty += 1
                if consecutive_empty >= 3:
                    # 连续 3 轮无就绪任务，可能存在死锁
                    logger.error("检测到可能的任务死锁，剩余 %d 个任务未完成", len(pending))
                    for st in pending:
                        st.status = "failed"
                        st.error = "任务调度死锁"
                    await self.broadcast({
                        "type": "log",
                        "source": "调度器",
                        "target": "错误",
                        "message": "检测到任务死锁，{} 个任务标记为失败".format(len(pending))
                    })
                    break

                logger.debug("第 %d 轮: 无就绪任务，%d 个待处理", round_num, len(pending))
                continue

            consecutive_empty = 0  # 重置计数
            logger.info("第 %d 轮: 执行 %d 个就绪任务", round_num, len(ready))
            await self.broadcast({
                "type": "log",
                "source": "调度器",
                "target": "执行",
                "message": "第 {} 轮: 执行 {} 个就绪任务".format(round_num, len(ready))
            })

            coros = [self._exec_one(project, st) for st in ready]
            results = await asyncio.gather(*coros, return_exceptions=True)

            for i, st in enumerate(ready):
                if isinstance(results[i], Exception):
                    st.status = "failed"
                    st.error = str(results[i])
                    logger.error("任务 '%s' 执行失败: %s", st.title, str(results[i])[:100])
                    await self.broadcast({
                        "type": "log",
                        "source": "系统",
                        "target": st.assigned_to,
                        "message": "任务失败: {}".format(str(results[i])[:100])
                    })
                elif st.status == "review" and st.needs_review:
                    await self._review_task(project, st)

    async def _execute_subtasks(self, project: Project, subtasks: list):
        """执行指定的子任务列表（用于修订流程）"""
        max_rounds = 5
        consecutive_empty = 0

        for round_num in range(1, max_rounds + 1):
            # 只从指定的 subtasks 中找就绪的
            ready = []
            for st in subtasks:
                if st.status in ("done", "failed"):
                    continue
                if st.status in ("pending", "assigned", "revision"):
                    deps_ok = True
                    for dep_id in st.dependencies:
                        found = any(d.id == dep_id and d.status == "done" for d in project.subtasks)
                        if not found:
                            deps_ok = False
                            break
                    if deps_ok:
                        ready.append(st)

            if not ready:
                pending = [st for st in subtasks if st.status not in ("done", "failed")]
                if not pending:
                    logger.info("修订任务全部完成")
                    break
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    logger.error("修订任务调度死锁，%d 个任务未完成", len(pending))
                    for st in pending:
                        st.status = "failed"
                        st.error = "任务调度死锁"
                    break
                continue

            consecutive_empty = 0
            logger.info("修订第 %d 轮: 执行 %d 个就绪任务", round_num, len(ready))
            await self.broadcast({
                "type": "log",
                "source": "调度器",
                "target": "修订执行",
                "message": "第 {} 轮: 返工 {} 个任务".format(round_num, len(ready))
            })

            coros = [self._exec_one(project, st) for st in ready]
            results = await asyncio.gather(*coros, return_exceptions=True)

            for i, st in enumerate(ready):
                if isinstance(results[i], Exception):
                    st.status = "failed"
                    st.error = str(results[i])
                    logger.error("修订任务 '%s' 失败: %s", st.title, str(results[i])[:100])
                elif st.status == "review" and st.needs_review:
                    await self._review_task(project, st)


    async def _execute_project_with_heartbeat(self, project: Project):
        """执行项目，带心跳监控"""
        max_rounds = 10
        consecutive_empty = 0
        task_start_times = {}  # task_id -> start_time

        for round_num in range(1, max_rounds + 1):
            ready = self._get_ready(project)

            if not ready:
                pending = [st for st in project.subtasks if st.status not in ("done", "failed")]
                if not pending:
                    logger.info("所有任务已完成")
                    break
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    logger.error("检测到可能的任务死锁，剩余 %d 个任务未完成", len(pending))
                    for st in pending:
                        st.status = "failed"
                        st.error = "任务调度死锁"
                    await self.broadcast({
                        "type": "log",
                        "source": "调度器",
                        "target": "错误",
                        "message": "检测到任务死锁，{} 个任务标记为失败".format(len(pending))
                    })
                    break
                logger.debug("第 %d 轮: 无就绪任务，%d 个待处理", round_num, len(pending))
                continue

            consecutive_empty = 0
            logger.info("第 %d 轮: 执行 %d 个就绪任务", round_num, len(ready))
            await self.broadcast({
                "type": "log",
                "source": "调度器",
                "target": "执行",
                "message": "第 {} 轮: 执行 {} 个就绪任务".format(round_num, len(ready))
            })

            # 记录任务开始时间
            for st in ready:
                task_start_times[st.id] = time.time()

            coros = [self._exec_one(project, st) for st in ready]
            results = await asyncio.gather(*coros, return_exceptions=True)

            for i, st in enumerate(ready):
                if isinstance(results[i], Exception):
                    st.status = "failed"
                    st.error = str(results[i])
                    elapsed = time.time() - task_start_times.get(st.id, time.time())
                    logger.error("任务 '%s' 执行失败 (%.1fs): %s", st.title, elapsed, str(results[i])[:100])
                    await self.broadcast({
                        "type": "log",
                        "source": "系统",
                        "target": st.assigned_to,
                        "message": "任务失败 ({}): {}".format(self._format_time(elapsed), str(results[i])[:100])
                    })
                elif st.status == "review" and st.needs_review:
                    await self._review_task(project, st)

    def _diagnose_timeout(self, project: Project) -> TimeoutDiagnosis:
        """诊断项目超时原因"""
        now = time.time()
        pending_tasks = [st for st in project.subtasks if st.status not in ("done", "failed")]
        done_tasks = [st for st in project.subtasks if st.status == "done"]

        # 检查是否有卡死的代理
        for agent_id, agent in self.agents.items():
            if hasattr(agent, '_last_cli_diagnosis') and agent._last_cli_diagnosis:
                if "卡死" in agent._last_cli_diagnosis:
                    # 找到卡死代理正在执行的任务
                    stuck_task = None
                    for st in pending_tasks:
                        if st.assigned_to == agent_id and st.status == "in_progress":
                            stuck_task = st
                            break
                    return TimeoutDiagnosis(
                        reason="stuck",
                        task_id=stuck_task.id if stuck_task else "",
                        task_title=stuck_task.title if stuck_task else "",
                        agent_id=agent_id,
                        elapsed=now - (stuck_task.started_at if stuck_task else now),
                        cli_diagnosis=agent._last_cli_diagnosis,
                        suggestion="retry"
                    )

        # 检查是否所有任务都在等依赖（死锁）
        if pending_tasks and all(st.status == "pending" for st in pending_tasks):
            return TimeoutDiagnosis(
                reason="deadlock",
                task_id=pending_tasks[0].id,
                task_title=pending_tasks[0].title,
                elapsed=0,
                suggestion="abort"
            )

        # 检查是否有任务执行了很久
        long_tasks = [st for st in pending_tasks if st.started_at and (now - st.started_at) > 120]
        if long_tasks:
            st = long_tasks[0]
            return TimeoutDiagnosis(
                reason="slow",
                task_id=st.id,
                task_title=st.title,
                agent_id=st.assigned_to,
                elapsed=now - st.started_at,
                suggestion="split" if len(done_tasks) < len(pending_tasks) else "retry"
            )

        # 默认
        return TimeoutDiagnosis(
            reason="unknown",
            task_id=pending_tasks[0].id if pending_tasks else "",
            task_title=pending_tasks[0].title if pending_tasks else "",
            elapsed=0,
            suggestion="retry"
        )

    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        if seconds < 60:
            return "{:.0f}s".format(seconds)
        elif seconds < 3600:
            return "{:.0f}m{:.0f}s".format(seconds // 60, seconds % 60)
        else:
            return "{:.1f}h".format(seconds / 3600)


    def _get_ready(self, project: Project) -> List[SubTask]:
        """获取就绪的子任务列表"""
        ready = []
        for st in project.subtasks:
            if st.status in ("done", "failed"):
                continue
            if st.status in ("pending", "assigned", "revision"):
                deps_ok = True
                for dep_id in st.dependencies:
                    found = any(d.id == dep_id and d.status == "done" for d in project.subtasks)
                    if not found:
                        deps_ok = False
                        break
                if deps_ok:
                    ready.append(st)
        return ready

    async def _exec_one(self, project: Project, subtask: SubTask):
        """执行单个子任务"""
        agent = self.agents.get(subtask.assigned_to)
        if not agent:
            subtask.status = "failed"
            subtask.error = "未找到代理: {}".format(subtask.assigned_to)
            logger.error("代理未找到: %s (任务: %s)", subtask.assigned_to, subtask.title)
            return

        subtask.status = "in_progress"
        subtask.started_at = time.time()
        logger.info("开始执行任务: %s (代理: %s)", subtask.title, subtask.assigned_to)

        await self.broadcast({
            "type": "task_status",
            "task_id": subtask.id,
            "status": "in_progress",
            "assigned_to": subtask.assigned_to
        })
        await self.broadcast({
            "type": "agent_status",
            "agent": subtask.assigned_to,
            "status": "working",
            "task": subtask.title
        })

        try:
            result = await agent.execute(subtask, project)
            subtask.result = result

            if subtask.needs_review:
                subtask.status = "review"
                await self.broadcast({
                    "type": "task_status",
                    "task_id": subtask.id,
                    "status": "review",
                    "message": "等待审查"
                })
            else:
                subtask.status = "done"
                subtask.completed_at = time.time()
                dur = subtask.completed_at - subtask.started_at
                logger.info("任务完成: %s (%.2f 秒)", subtask.title, dur)
                await self.broadcast({
                    "type": "task_status",
                    "task_id": subtask.id,
                    "status": "done",
                    "duration": dur
                })
                await self.broadcast({
                    "type": "task_result",
                    "task_id": subtask.id,
                    "agent": subtask.assigned_to,
                    "result": result[:500],
                    "duration": dur
                })
        except Exception as e:
            subtask.status = "failed"
            subtask.error = str(e)
            logger.error("任务执行异常 [%s]: %s", subtask.title, str(e), exc_info=True)
            await self.broadcast({
                "type": "task_status",
                "task_id": subtask.id,
                "status": "failed",
                "error": str(e)[:200]
            })
        finally:
            await self.broadcast({
                "type": "agent_status",
                "agent": subtask.assigned_to,
                "status": "idle"
            })

    async def _review_task(self, project: Project, subtask: SubTask):
        """安排审查任务"""
        reviewer = self.agents.get("openclaw")
        if not reviewer:
            logger.warning("审查代理不可用，跳过审查: %s", subtask.title)
            subtask.status = "done"
            subtask.completed_at = time.time()
            return

        logger.info("安排审查: %s -> OpenClaw", subtask.title)
        await self.broadcast({
            "type": "log",
            "source": "调度器",
            "target": "审查",
            "message": "安排审查: {} -> OpenClaw".format(subtask.title)
        })
        await self.broadcast({
            "type": "agent_status",
            "agent": "openclaw",
            "status": "reviewing",
            "task": "审查: {}".format(subtask.title)
        })

        review_task = SubTask(
            id="review-{}".format(subtask.id),
            title="审查: {}".format(subtask.title),
            description="审查 {} 的产出".format(subtask.assigned_to),
            assigned_to="openclaw",
            dependencies=[subtask.id],
            needs_review=False,
        )
        review_task.status = "in_progress"
        review_task.started_at = time.time()

        try:
            await reviewer.execute(review_task, project)

            if subtask.review_result:
                if subtask.review_result.approved:
                    subtask.status = "done"
                    subtask.completed_at = time.time()
                    logger.info("审查通过: %s (评分: %d)", subtask.title, subtask.review_result.score)
                    await self.broadcast({
                        "type": "task_status",
                        "task_id": subtask.id,
                        "status": "done",
                        "review_score": subtask.review_result.score,
                        "message": "审查通过 (评分: {})".format(subtask.review_result.score)
                    })
                else:
                    if subtask.retry_count < subtask.max_retries:
                        subtask.retry_count += 1
                        subtask.status = "revision"
                        logger.info("审查未通过，第 %d 次修订: %s", subtask.retry_count, subtask.title)
                        await self.broadcast({
                            "type": "task_status",
                            "task_id": subtask.id,
                            "status": "revision",
                            "review_issues": subtask.review_result.issues,
                            "message": "审查未通过，第 {} 次修订".format(subtask.retry_count)
                        })
                        await self.broadcast({
                            "type": "log",
                            "source": "审查员",
                            "target": subtask.assigned_to,
                            "message": "需要修改: {}".format("; ".join(subtask.review_result.issues[:3]))
                        })
                    else:
                        subtask.status = "done"
                        subtask.completed_at = time.time()
                        logger.warning("已达最大修订次数: %s", subtask.title)
                        await self.broadcast({
                            "type": "task_status",
                            "task_id": subtask.id,
                            "status": "done",
                            "message": "已达最大修订次数，接受当前版本"
                        })
            else:
                subtask.status = "done"
                subtask.completed_at = time.time()
                logger.info("审查完成（无结果）: %s", subtask.title)
        except Exception as e:
            subtask.status = "done"
            subtask.completed_at = time.time()
            logger.error("审查出错 [%s]: %s", subtask.title, str(e))
            await self.broadcast({
                "type": "log",
                "source": "系统",
                "target": "审查",
                "message": "审查出错: {}".format(str(e)[:100])
            })
        finally:
            await self.broadcast({
                "type": "agent_status",
                "agent": "openclaw",
                "status": "idle"
            })

    def _st_dict(self, st: SubTask) -> dict:
        """将 SubTask 转换为字典"""
        return {
            "id": st.id,
            "title": st.title,
            "description": st.description,
            "assigned_to": st.assigned_to,
            "status": st.status,
            "dependencies": st.dependencies,
            "needs_review": st.needs_review
        }
