"""
服务器模块测试

测试错误处理、消息验证、边界情况
"""
import asyncio
import json
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from server import (
    _validate_message,
    StudioServer,
    VALID_MESSAGE_TYPES,
    MAX_MESSAGE_SIZE,
)


class TestValidateMessage:
    """消息验证函数测试"""

    def test_valid_start_project(self):
        """测试有效的 start_project 消息"""
        data = {"type": "start_project", "requirement": "做一个网站"}
        assert _validate_message(data) is None

    def test_valid_execute_task(self):
        """测试有效的 execute_task 消息"""
        data = {"type": "execute_task", "prompt": "写一个排序算法"}
        assert _validate_message(data) is None

    def test_valid_ping(self):
        """测试有效的 ping 消息"""
        data = {"type": "ping"}
        assert _validate_message(data) is None

    def test_non_dict_input(self):
        """测试非字典输入"""
        assert _validate_message("not a dict") == "消息必须是 JSON 对象"
        assert _validate_message([1, 2, 3]) == "消息必须是 JSON 对象"
        assert _validate_message(42) == "消息必须是 JSON 对象"
        assert _validate_message(None) == "消息必须是 JSON 对象"

    def test_missing_type_field(self):
        """测试缺少 type 字段"""
        data = {"requirement": "做一个网站"}
        assert _validate_message(data) == "消息缺少 'type' 字段"

    def test_unknown_message_type(self):
        """测试未知消息类型"""
        data = {"type": "unknown_type"}
        assert "未知的消息类型" in _validate_message(data)

    def test_start_project_empty_requirement(self):
        """测试 start_project 空需求"""
        data = {"type": "start_project", "requirement": ""}
        assert "缺少有效的 'requirement'" in _validate_message(data)

    def test_start_project_whitespace_requirement(self):
        """测试 start_project 空白需求"""
        data = {"type": "start_project", "requirement": "   "}
        assert "缺少有效的 'requirement'" in _validate_message(data)

    def test_start_project_missing_requirement(self):
        """测试 start_project 缺少 requirement"""
        data = {"type": "start_project"}
        assert "缺少有效的 'requirement'" in _validate_message(data)

    def test_start_project_non_string_requirement(self):
        """测试 start_project 非字符串 requirement"""
        data = {"type": "start_project", "requirement": 123}
        assert "缺少有效的 'requirement'" in _validate_message(data)

    def test_execute_task_empty_prompt(self):
        """测试 execute_task 空 prompt"""
        data = {"type": "execute_task", "prompt": ""}
        assert "缺少有效的 'prompt'" in _validate_message(data)

    def test_execute_task_missing_prompt(self):
        """测试 execute_task 缺少 prompt"""
        data = {"type": "execute_task"}
        assert "缺少有效的 'prompt'" in _validate_message(data)

    def test_message_size_limit(self):
        """测试消息大小限制"""
        data = {"type": "ping"}
        # 刚好超过限制
        error = _validate_message(data, raw_size=MAX_MESSAGE_SIZE + 1)
        assert "消息大小超过限制" in error

    def test_message_size_at_limit(self):
        """测试消息大小刚好在限制内"""
        data = {"type": "ping"}
        error = _validate_message(data, raw_size=MAX_MESSAGE_SIZE)
        assert error is None

    def test_message_size_zero(self):
        """测试零大小消息"""
        data = {"type": "ping"}
        error = _validate_message(data, raw_size=0)
        assert error is None


class TestStudioServerInit:
    """服务器初始化测试"""

    @patch('server.create_agents')
    def test_init_success(self, mock_create_agents):
        """测试成功初始化"""
        mock_agents = {
            "hermes": MagicMock(available=True, name="Hermes", icon="🎯"),
            "claude-code": MagicMock(available=True, name="Claude Code", icon="🤖"),
        }
        mock_create_agents.return_value = mock_agents
        server = StudioServer()
        assert len(server.agents) == 2
        assert len(server.clients) == 0
        assert len(server._active_projects) == 0

    @patch('server.create_agents')
    def test_init_agent_creation_failure(self, mock_create_agents):
        """测试代理创建失败"""
        from agents import AgentError
        mock_create_agents.side_effect = AgentError("创建失败")
        with pytest.raises(AgentError):
            StudioServer()


class TestBroadcast:
    """广播功能测试"""

    @patch('server.create_agents')
    def test_broadcast_empty_clients(self, mock_create_agents):
        """测试无客户端时广播不报错"""
        mock_create_agents.return_value = {"hermes": MagicMock(available=True)}
        server = StudioServer()
        # 不应抛出异常
        asyncio.run(server.broadcast({"type": "test"}))

    @patch('server.create_agents')
    def test_broadcast_non_dict_message(self, mock_create_agents):
        """测试广播非字典消息"""
        mock_create_agents.return_value = {"hermes": MagicMock(available=True)}
        server = StudioServer()
        # 不应抛出异常，只是警告
        asyncio.run(server.broadcast("not a dict"))

    @patch('server.create_agents')
    def test_broadcast_serialization_error(self, mock_create_agents):
        """测试消息序列化失败"""
        mock_create_agents.return_value = {"hermes": MagicMock(available=True)}
        server = StudioServer()
        # 无法序列化的对象
        asyncio.run(server.broadcast({"data": object()}))


class TestHandle:
    """消息处理测试"""

    @patch('server.create_agents')
    def test_handle_ping_responds_pong(self, mock_create_agents):
        """测试 ping 消息返回 pong"""
        mock_agents = {"hermes": MagicMock(available=True)}
        mock_create_agents.return_value = mock_agents
        server = StudioServer()

        mock_ws = AsyncMock()
        asyncio.run(server._handle({"type": "ping"}, mock_ws))

        # 验证发送了 pong 响应
        mock_ws.send.assert_called_once()
        sent_data = json.loads(mock_ws.send.call_args[0][0])
        assert sent_data["type"] == "pong"
        assert "timestamp" in sent_data

    @patch('server.create_agents')
    def test_handle_ping_no_websocket(self, mock_create_agents):
        """测试 ping 消息无 websocket 连接"""
        mock_create_agents.return_value = {"hermes": MagicMock(available=True)}
        server = StudioServer()
        # 不应抛出异常
        asyncio.run(server._handle({"type": "ping"}, None))

    @patch('server.create_agents')
    def test_handle_start_project_name_conflict(self, mock_create_agents):
        """测试项目名冲突"""
        mock_create_agents.return_value = {"hermes": MagicMock(available=True)}
        server = StudioServer()

        # 模拟一个活跃项目
        mock_task = MagicMock()
        mock_task.done.return_value = False
        server._active_projects["测试项目"] = mock_task

        mock_ws = AsyncMock()
        asyncio.run(server._handle({
            "type": "start_project",
            "name": "测试项目",
            "requirement": "做一个网站"
        }, mock_ws))

        # 应该发送错误消息
        mock_ws.send.assert_called_once()
        sent_data = json.loads(mock_ws.send.call_args[0][0])
        assert sent_data["type"] == "error"
        assert "已在执行中" in sent_data["message"]

    @patch('server.create_agents')
    def test_handle_start_project_done_task_allows_restart(self, mock_create_agents):
        """测试已完成的项目允许重新启动"""
        mock_create_agents.return_value = {"hermes": MagicMock(available=True)}
        server = StudioServer()

        # 模拟一个已完成的项目
        mock_task = MagicMock()
        mock_task.done.return_value = True
        server._active_projects["测试项目"] = mock_task

        mock_ws = AsyncMock()
        # 不应抛出异常，应该允许重新启动
        asyncio.run(server._handle({
            "type": "start_project",
            "name": "测试项目",
            "requirement": "做一个网站"
        }, mock_ws))

    @patch('server.create_agents')
    def test_handle_execute_task_name_conflict(self, mock_create_agents):
        """测试任务名冲突"""
        mock_create_agents.return_value = {"hermes": MagicMock(available=True)}
        server = StudioServer()

        mock_task = MagicMock()
        mock_task.done.return_value = False
        server._active_projects["排序算法"] = mock_task

        mock_ws = AsyncMock()
        asyncio.run(server._handle({
            "type": "execute_task",
            "prompt": "排序算法"
        }, mock_ws))

        mock_ws.send.assert_called_once()
        sent_data = json.loads(mock_ws.send.call_args[0][0])
        assert sent_data["type"] == "error"


class TestRunProject:
    """项目执行测试"""

    @patch('server.create_agents')
    def test_run_project_cleanup_on_completion(self, mock_create_agents):
        """测试项目完成后清理活跃项目"""
        mock_agents = {"hermes": MagicMock(available=True)}
        mock_create_agents.return_value = mock_agents
        server = StudioServer()

        # 添加一个模拟项目
        mock_task = MagicMock()
        server._active_projects["test-project"] = mock_task

        # 模拟 dispatcher.start_project 成功
        server.dispatcher = MagicMock()
        server.dispatcher.start_project = AsyncMock()

        asyncio.run(server._run_project("test-project", "需求"))

        # 项目应从活跃列表中移除
        assert "test-project" not in server._active_projects

    @patch('server.create_agents')
    def test_run_project_cleanup_on_error(self, mock_create_agents):
        """测试项目出错后清理活跃项目"""
        from dispatcher import DispatcherError

        mock_agents = {"hermes": MagicMock(available=True)}
        mock_create_agents.return_value = mock_agents
        server = StudioServer()

        server._active_projects["test-project"] = MagicMock()

        server.dispatcher = MagicMock()
        server.dispatcher.start_project = AsyncMock(side_effect=DispatcherError("调度错误"))

        asyncio.run(server._run_project("test-project", "需求"))

        assert "test-project" not in server._active_projects


class TestServerStart:
    """服务器启动测试"""

    @patch('server.create_agents')
    def test_invalid_port(self, mock_create_agents):
        """测试无效端口"""
        mock_create_agents.return_value = {"hermes": MagicMock(available=True)}
        server = StudioServer()

        with pytest.raises(ValueError, match="端口号"):
            asyncio.run(server.start(port=0))

        with pytest.raises(ValueError, match="端口号"):
            asyncio.run(server.start(port=-1))

        with pytest.raises(ValueError, match="端口号"):
            asyncio.run(server.start(port=70000))

    @patch('server.create_agents')
    def test_invalid_port_type(self, mock_create_agents):
        """测试端口类型错误"""
        mock_create_agents.return_value = {"hermes": MagicMock(available=True)}
        server = StudioServer()

        with pytest.raises(ValueError, match="端口号"):
            asyncio.run(server.start(port="8765"))

    @patch('server.create_agents')
    def test_invalid_host(self, mock_create_agents):
        """测试无效 host"""
        mock_create_agents.return_value = {"hermes": MagicMock(available=True)}
        server = StudioServer()

        with pytest.raises(ValueError, match="host"):
            asyncio.run(server.start(host=""))

        with pytest.raises(ValueError, match="host"):
            asyncio.run(server.start(host="   "))


class TestConstants:
    """常量测试"""

    def test_valid_message_types(self):
        """测试有效的消息类型集合"""
        assert "start_project" in VALID_MESSAGE_TYPES
        assert "execute_task" in VALID_MESSAGE_TYPES
        assert "ping" in VALID_MESSAGE_TYPES

    def test_max_message_size(self):
        """测试消息大小限制常量"""
        assert MAX_MESSAGE_SIZE > 0
        assert MAX_MESSAGE_SIZE == 1024 * 1024  # 1MB


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
