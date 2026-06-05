"""
AI工作室 - WebSocket服务器
"""
import asyncio
import json
import logging
import time
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import websockets
from typing import Set, Optional, Dict, Any
from agents import create_agents, AgentError
from dispatcher import StudioDispatcher, DispatcherError, ProjectTimeoutError


# ──────────────────────────────────────────────
# 消息验证
# ──────────────────────────────────────────────

VALID_MESSAGE_TYPES = {
    "start_project",
    "execute_task",
    "ping",
}

# 消息大小限制 (1MB)
MAX_MESSAGE_SIZE = 1 * 1024 * 1024

# 连接空闲超时 (秒)
CONNECTION_IDLE_TIMEOUT = 300


def _validate_message(data: Dict[str, Any], raw_size: int = 0) -> Optional[str]:
    """
    验证 WebSocket 消息格式

    Args:
        data: 解析后的消息数据
        raw_size: 原始消息字节大小

    Returns:
        None 如果消息有效，否则返回错误信息
    """
    if raw_size > MAX_MESSAGE_SIZE:
        return "消息大小超过限制 ({} bytes)".format(MAX_MESSAGE_SIZE)

    if not isinstance(data, dict):
        return "消息必须是 JSON 对象"

    msg_type = data.get("type")
    if not msg_type:
        return "消息缺少 'type' 字段"

    if msg_type not in VALID_MESSAGE_TYPES:
        return "未知的消息类型: {}".format(msg_type)

    if msg_type == "start_project":
        requirement = data.get("requirement", "")
        if not requirement or not isinstance(requirement, str) or not requirement.strip():
            return "start_project 消息缺少有效的 'requirement' 字段"

    if msg_type == "execute_task":
        prompt = data.get("prompt", "")
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            return "execute_task 消息缺少有效的 'prompt' 字段"

    return None


class StudioServer:
    """WebSocket 服务器 - 管理客户端连接和消息路由"""

    def __init__(self):
        self.clients: Set = set()
        self._active_projects: Dict[str, asyncio.Task] = {}
        logger.info("初始化服务器...")

        try:
            self.agents = create_agents()
            self.dispatcher = StudioDispatcher(self.agents)
            self.dispatcher.set_broadcaster(self.broadcast)
            logger.info("服务器初始化完成: %d 个代理", len(self.agents))
        except Exception as e:
            logger.critical("服务器初始化失败: %s", str(e), exc_info=True)
            raise

    async def broadcast(self, message: dict):
        """广播消息到所有连接的客户端"""
        if not self.clients:
            return

        if not isinstance(message, dict):
            logger.warning("broadcast: 消息不是字典: %s", type(message).__name__)
            return

        try:
            msg = json.dumps(message, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            logger.error("消息序列化失败: %s", str(e))
            return

        dead = set()
        for c in self.clients:
            try:
                await c.send(msg)
            except websockets.exceptions.ConnectionClosed:
                dead.add(c)
            except Exception as e:
                logger.warning("发送消息到客户端失败: %s", str(e))
                dead.add(c)

        if dead:
            self.clients -= dead
            logger.debug("清理 %d 个断开的客户端连接", len(dead))

    async def handler(self, websocket):
        """处理单个 WebSocket 连接"""
        client_id = id(websocket)
        self.clients.add(websocket)
        logger.info("新客户端连接: #%d (共 %d 个)", client_id, len(self.clients))

        await self.broadcast({
            "type": "log",
            "source": "系统",
            "target": "连接",
            "message": "新客户端连接 (共 {} 个)".format(len(self.clients))
        })

        # 发送代理状态 + 可用性
        try:
            for aid, agent in self.agents.items():
                await websocket.send(json.dumps({
                    "type": "agent_status",
                    "agent": aid,
                    "status": agent.status,
                    "available": agent.available
                }, ensure_ascii=False))
        except websockets.exceptions.ConnectionClosed:
            logger.warning("客户端在发送初始状态时断开: #%d", client_id)
            self.clients.discard(websocket)
            return

        try:
            async for message in websocket:
                try:
                    # 消息大小检查
                    msg_size = len(message.encode("utf-8")) if isinstance(message, str) else len(message)
                    if msg_size > MAX_MESSAGE_SIZE:
                        logger.warning("消息过大 [%d]: %d bytes", client_id, msg_size)
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "消息大小超过限制"
                        }, ensure_ascii=False))
                        continue

                    data = json.loads(message)
                    validation_error = _validate_message(data, raw_size=msg_size)
                    if validation_error:
                        logger.warning("消息验证失败 [%d]: %s", client_id, validation_error)
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": validation_error
                        }, ensure_ascii=False))
                        continue
                    await self._handle(data, websocket)
                except json.JSONDecodeError as e:
                    logger.warning("JSON 解析失败 [%d]: %s", client_id, str(e))
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "无效的 JSON 格式"
                    }, ensure_ascii=False))
                except Exception as e:
                    logger.error("处理消息异常 [%d]: %s", client_id, str(e), exc_info=True)
        except websockets.exceptions.ConnectionClosed as e:
            logger.info("客户端断开连接: #%d (原因: %s)", client_id, str(e))
        except Exception as e:
            logger.error("WebSocket 处理异常 [%d]: %s", client_id, str(e), exc_info=True)
        finally:
            self.clients.discard(websocket)
            logger.info("客户端已移除: #%d (剩余 %d 个)", client_id, len(self.clients))

    async def _handle(self, data: dict, websocket=None):
        """处理已验证的消息"""
        msg_type = data.get("type")

        if msg_type == "start_project":
            name = data.get("name", "未命名")
            req = data.get("requirement", "")
            if req:
                # 检查项目名冲突
                if name in self._active_projects and not self._active_projects[name].done():
                    logger.warning("项目名冲突: %s", name)
                    if websocket:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "项目 '{}' 已在执行中，请等待完成或使用不同名称".format(name)
                        }, ensure_ascii=False))
                    return
                logger.info("收到项目请求: %s", name)
                task = asyncio.create_task(self._run_project(name, req))
                self._active_projects[name] = task

        elif msg_type == "execute_task":
            prompt = data.get("prompt", "")
            if prompt:
                task_name = prompt[:30]
                # 检查任务名冲突
                if task_name in self._active_projects and not self._active_projects[task_name].done():
                    logger.warning("任务名冲突: %s", task_name)
                    if websocket:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "任务 '{}' 已在执行中".format(task_name)
                        }, ensure_ascii=False))
                    return
                logger.info("收到任务请求: %s...", task_name)
                task = asyncio.create_task(self._run_project(task_name, prompt))
                self._active_projects[task_name] = task

        elif msg_type == "ping":
            logger.debug("收到 ping 消息")
            if websocket:
                try:
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "timestamp": time.time()
                    }, ensure_ascii=False))
                except Exception as e:
                    logger.warning("发送 pong 失败: %s", str(e))

    async def _run_project(self, name: str, requirement: str):
        """执行项目（包装异常处理）"""
        try:
            await self.dispatcher.start_project(name, requirement)
            logger.info("项目完成: %s", name)
        except ProjectTimeoutError as e:
            logger.error("项目超时 [%s]: %s", name, str(e))
            await self.broadcast({
                "type": "log",
                "source": "系统",
                "target": "超时",
                "message": "项目执行超时: {}".format(str(e)[:200])
            })
            await self.broadcast({
                "type": "phase_change",
                "phase": "error",
                "message": "项目执行超时"
            })
        except DispatcherError as e:
            logger.error("项目调度错误 [%s]: %s", name, str(e))
            await self.broadcast({
                "type": "log",
                "source": "系统",
                "target": "错误",
                "message": "项目执行失败: {}".format(str(e)[:200])
            })
            await self.broadcast({
                "type": "phase_change",
                "phase": "error",
                "message": "项目执行出错: {}".format(str(e)[:100])
            })
        except AgentError as e:
            logger.error("代理错误 [%s]: %s", name, str(e))
            await self.broadcast({
                "type": "log",
                "source": "系统",
                "target": "错误",
                "message": "代理执行失败: {}".format(str(e)[:200])
            })
            await self.broadcast({
                "type": "phase_change",
                "phase": "error",
                "message": "代理执行出错"
            })
        except Exception as e:
            logger.error("项目执行异常 [%s]: %s", name, str(e), exc_info=True)
            await self.broadcast({
                "type": "log",
                "source": "系统",
                "target": "错误",
                "message": "项目执行失败: {}".format(str(e)[:200])
            })
            await self.broadcast({
                "type": "phase_change",
                "phase": "error",
                "message": "项目执行出错"
            })
        finally:
            self._active_projects.pop(name, None)

    async def _cancel_active_projects(self):
        """取消所有活跃项目（优雅关闭时调用）"""
        if not self._active_projects:
            return
        logger.info("取消 %d 个活跃项目...", len(self._active_projects))
        for name, task in self._active_projects.items():
            if not task.done():
                task.cancel()
                logger.info("已取消项目: %s", name)
        self._active_projects.clear()

    async def start(self, host: str = "0.0.0.0", port: int = 8765):
        """启动 WebSocket 服务器"""
        # 验证端口
        if not isinstance(port, int) or port < 1 or port > 65535:
            logger.error("无效的端口号: %s", port)
            raise ValueError("端口号必须是 1-65535 之间的整数")

        # 验证 host
        if not isinstance(host, str) or not host.strip():
            logger.error("无效的 host: %s", host)
            raise ValueError("host 必须是非空字符串")

        print("=" * 50)
        print("  AI工作室服务器")
        print("  WebSocket: ws://{}:{}".format(host, port))
        print("  前端: 打开 frontend/index.html")
        # 显示代理可用性
        for aid, agent in self.agents.items():
            status = "可用" if agent.available else "未安装(使用演示模式)"
            print("  {} {}: {}".format(agent.icon, agent.name, status))
        print("=" * 50)

        logger.info("启动 WebSocket 服务器: %s:%d", host, port)

        try:
            async with websockets.serve(self.handler, host, port):
                logger.info("服务器已启动，等待连接...")
                await asyncio.Future()
        except OSError as e:
            logger.critical("服务器启动失败: %s", str(e))
            raise
        except KeyboardInterrupt:
            logger.info("服务器收到中断信号，正在关闭...")
        except asyncio.CancelledError:
            logger.info("服务器任务被取消")
        finally:
            await self._cancel_active_projects()
            logger.info("服务器已关闭")


if __name__ == "__main__":
    try:
        server = StudioServer()
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        logger.critical("服务器启动失败: %s", str(e), exc_info=True)
        sys.exit(1)
