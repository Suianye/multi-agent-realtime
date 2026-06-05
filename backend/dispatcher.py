"""
AI工作室 - 任务调度器
管理项目生命周期: 需求分解 -> 任务分配 -> 执行 -> 审查 -> 修订 -> 完成
"""
import asyncio
import time
import uuid
from typing import Dict, List, Optional, Callable
from agents import BaseAgent, Project, SubTask, ReviewResult, create_agents


class StudioDispatcher:
    def __init__(self, agents: Dict[str, BaseAgent]):
        self.agents = agents
        self.projects: Dict[str, Project] = {}
        self._broadcast: Optional[Callable] = None

    def set_broadcaster(self, broadcast_fn):
        self._broadcast = broadcast_fn
        for agent in self.agents.values():
            agent.set_broadcaster(broadcast_fn)

    async def broadcast(self, message):
        if self._broadcast:
            await self._broadcast(message)

    async def start_project(self, name, requirement):
        project_id = "proj-{}".format(uuid.uuid4().hex[:8])
        project = Project(id=project_id, name=name, description=requirement)
        self.projects[project_id] = project

        await self.broadcast({"type": "project_created", "project_id": project_id, "name": name, "requirement": requirement})

        # 阶段1: 需求分解
        await self.broadcast({"type": "phase_change", "phase": "planning", "message": "项目经理正在分析需求..."})
        project.status = "planning"

        pm = self.agents["hermes"]
        subtask_dicts = await pm.decompose_task(requirement, project)

        project.subtasks = []
        for st_dict in subtask_dicts:
            st = SubTask(
                id=st_dict.get("id", "task-{}".format(uuid.uuid4().hex[:6])),
                title=st_dict.get("title", "未命名"),
                description=st_dict.get("description", ""),
                assigned_to=st_dict.get("assigned_to", "claude-code"),
                dependencies=st_dict.get("dependencies", []),
                needs_review=st_dict.get("needs_review", True),
            )
            project.subtasks.append(st)

        await self.broadcast({"type": "task_breakdown", "project_id": project_id, "subtasks": [self._st_dict(st) for st in project.subtasks]})

        # 阶段2: 执行
        project.status = "executing"
        await self.broadcast({"type": "phase_change", "phase": "executing", "message": "开始执行 {} 个子任务".format(len(project.subtasks))})
        await self._execute_project(project)

        # 阶段3: 完成
        project.status = "done"
        done_count = len([st for st in project.subtasks if st.status == "done"])
        fail_count = len([st for st in project.subtasks if st.status == "failed"])

        await self.broadcast({"type": "project_complete", "project_id": project_id, "success": fail_count == 0, "total_tasks": len(project.subtasks), "completed": done_count, "failed": fail_count})
        await self.broadcast({"type": "phase_change", "phase": "done", "message": "项目完成! {}/{} 任务成功".format(done_count, len(project.subtasks))})
        return project

    async def _execute_project(self, project):
        max_rounds = 10
        for round_num in range(1, max_rounds + 1):
            ready = self._get_ready(project)
            if not ready:
                pending = [st for st in project.subtasks if st.status not in ("done", "failed")]
                if not pending:
                    break
                for st in pending:
                    st.status = "failed"
                    st.error = "依赖任务未完成"
                break

            await self.broadcast({"type": "log", "source": "调度器", "target": "执行", "message": "第 {} 轮: 执行 {} 个就绪任务".format(round_num, len(ready))})

            coros = [self._exec_one(project, st) for st in ready]
            results = await asyncio.gather(*coros, return_exceptions=True)

            for i, st in enumerate(ready):
                if isinstance(results[i], Exception):
                    st.status = "failed"
                    st.error = str(results[i])
                    await self.broadcast({"type": "log", "source": "系统", "target": st.assigned_to, "message": "任务失败: {}".format(str(results[i])[:100])})
                elif st.status == "review" and st.needs_review:
                    await self._review_task(project, st)

    def _get_ready(self, project):
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

    async def _exec_one(self, project, subtask):
        agent = self.agents.get(subtask.assigned_to)
        if not agent:
            subtask.status = "failed"
            subtask.error = "未找到代理: {}".format(subtask.assigned_to)
            return

        subtask.status = "in_progress"
        subtask.started_at = time.time()

        await self.broadcast({"type": "task_status", "task_id": subtask.id, "status": "in_progress", "assigned_to": subtask.assigned_to})
        await self.broadcast({"type": "agent_status", "agent": subtask.assigned_to, "status": "working", "task": subtask.title})

        try:
            result = await agent.execute(subtask, project)
            subtask.result = result

            if subtask.needs_review:
                subtask.status = "review"
                await self.broadcast({"type": "task_status", "task_id": subtask.id, "status": "review", "message": "等待审查"})
            else:
                subtask.status = "done"
                subtask.completed_at = time.time()
                dur = subtask.completed_at - subtask.started_at
                await self.broadcast({"type": "task_status", "task_id": subtask.id, "status": "done", "duration": dur})
                await self.broadcast({"type": "task_result", "task_id": subtask.id, "agent": subtask.assigned_to, "result": result[:500], "duration": dur})
        except Exception as e:
            subtask.status = "failed"
            subtask.error = str(e)
            await self.broadcast({"type": "task_status", "task_id": subtask.id, "status": "failed", "error": str(e)[:200]})
        finally:
            await self.broadcast({"type": "agent_status", "agent": subtask.assigned_to, "status": "idle"})

    async def _review_task(self, project, subtask):
        reviewer = self.agents.get("openclaw")
        if not reviewer:
            subtask.status = "done"
            subtask.completed_at = time.time()
            return

        await self.broadcast({"type": "log", "source": "调度器", "target": "审查", "message": "安排审查: {} -> OpenClaw".format(subtask.title)})
        await self.broadcast({"type": "agent_status", "agent": "openclaw", "status": "reviewing", "task": "审查: {}".format(subtask.title)})

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
                    await self.broadcast({"type": "task_status", "task_id": subtask.id, "status": "done", "review_score": subtask.review_result.score, "message": "审查通过 (评分: {})".format(subtask.review_result.score)})
                else:
                    if subtask.retry_count < subtask.max_retries:
                        subtask.retry_count += 1
                        subtask.status = "revision"
                        await self.broadcast({"type": "task_status", "task_id": subtask.id, "status": "revision", "review_issues": subtask.review_result.issues, "message": "审查未通过，第 {} 次修订".format(subtask.retry_count)})
                        await self.broadcast({"type": "log", "source": "审查员", "target": subtask.assigned_to, "message": "需要修改: {}".format("; ".join(subtask.review_result.issues[:3]))})
                    else:
                        subtask.status = "done"
                        subtask.completed_at = time.time()
                        await self.broadcast({"type": "task_status", "task_id": subtask.id, "status": "done", "message": "已达最大修订次数，接受当前版本"})
            else:
                subtask.status = "done"
                subtask.completed_at = time.time()
        except Exception as e:
            subtask.status = "done"
            subtask.completed_at = time.time()
            await self.broadcast({"type": "log", "source": "系统", "target": "审查", "message": "审查出错: {}".format(str(e)[:100])})
        finally:
            await self.broadcast({"type": "agent_status", "agent": "openclaw", "status": "idle"})

    def _st_dict(self, st):
        return {"id": st.id, "title": st.title, "description": st.description, "assigned_to": st.assigned_to, "status": st.status, "dependencies": st.dependencies, "needs_review": st.needs_review}
