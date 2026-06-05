"""
调度器模块测试

测试错误处理、依赖验证、边界情况
"""
import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents import (
    BaseAgent, Project, SubTask, ReviewResult,
    InvalidTaskError, AgentNotAvailableError, AgentError,
)
from dispatcher import (
    StudioDispatcher,
    DispatcherError,
    CircularDependencyError,
    MissingDependencyError,
    ProjectNotFoundError,
    ProjectTimeoutError,
    _validate_project_name,
    _validate_requirement,
    _detect_circular_dependencies,
    _validate_task_dependencies,
    PROJECT_EXECUTION_TIMEOUT,
)


# ──────────────────────────────────────────────
# 输入验证测试
# ──────────────────────────────────────────────

class TestValidateProjectName:
    """项目名称验证测试"""

    def test_valid_name(self):
        """测试有效名称"""
        _validate_project_name("我的项目")  # 不应抛出异常

    def test_non_string_name(self):
        """测试非字符串名称"""
        with pytest.raises(InvalidTaskError, match="字符串"):
            _validate_project_name(123)

    def test_empty_name(self):
        """测试空名称"""
        with pytest.raises(InvalidTaskError, match="不能为空"):
            _validate_project_name("")

    def test_whitespace_name(self):
        """测试空白名称"""
        with pytest.raises(InvalidTaskError, match="不能为空"):
            _validate_project_name("   ")

    def test_none_name(self):
        """测试 None 名称"""
        with pytest.raises(InvalidTaskError, match="字符串"):
            _validate_project_name(None)


class TestValidateRequirement:
    """需求描述验证测试"""

    def test_valid_requirement(self):
        """测试有效需求"""
        _validate_requirement("做一个网站")  # 不应抛出异常

    def test_non_string_requirement(self):
        """测试非字符串需求"""
        with pytest.raises(InvalidTaskError, match="字符串"):
            _validate_requirement([])

    def test_empty_requirement(self):
        """测试空需求"""
        with pytest.raises(InvalidTaskError, match="不能为空"):
            _validate_requirement("")

    def test_none_requirement(self):
        """测试 None 需求"""
        with pytest.raises(InvalidTaskError, match="字符串"):
            _validate_requirement(None)


# ──────────────────────────────────────────────
# 依赖检测测试
# ──────────────────────────────────────────────

class TestCircularDependencyDetection:
    """循环依赖检测测试"""

    def test_no_dependencies(self):
        """测试无依赖"""
        subtasks = [
            SubTask(id="t1", title="任务1", description="", assigned_to="claude-code"),
            SubTask(id="t2", title="任务2", description="", assigned_to="claude-code"),
        ]
        assert _detect_circular_dependencies(subtasks) is None

    def test_linear_dependencies(self):
        """测试线性依赖（无循环）"""
        subtasks = [
            SubTask(id="t1", title="任务1", description="", assigned_to="claude-code"),
            SubTask(id="t2", title="任务2", description="", assigned_to="claude-code", dependencies=["t1"]),
            SubTask(id="t3", title="任务3", description="", assigned_to="claude-code", dependencies=["t2"]),
        ]
        assert _detect_circular_dependencies(subtasks) is None

    def test_simple_circular_dependency(self):
        """测试简单循环依赖"""
        subtasks = [
            SubTask(id="t1", title="任务1", description="", assigned_to="claude-code", dependencies=["t2"]),
            SubTask(id="t2", title="任务2", description="", assigned_to="claude-code", dependencies=["t1"]),
        ]
        result = _detect_circular_dependencies(subtasks)
        assert result is not None
        assert len(result) >= 3  # t1 -> t2 -> t1

    def test_three_way_circular_dependency(self):
        """测试三方循环依赖"""
        subtasks = [
            SubTask(id="t1", title="任务1", description="", assigned_to="claude-code", dependencies=["t2"]),
            SubTask(id="t2", title="任务2", description="", assigned_to="claude-code", dependencies=["t3"]),
            SubTask(id="t3", title="任务3", description="", assigned_to="claude-code", dependencies=["t1"]),
        ]
        result = _detect_circular_dependencies(subtasks)
        assert result is not None

    def test_empty_subtasks(self):
        """测试空子任务列表"""
        assert _detect_circular_dependencies([]) is None

    def test_single_task_no_cycle(self):
        """测试单个任务无循环"""
        subtasks = [
            SubTask(id="t1", title="任务1", description="", assigned_to="claude-code"),
        ]
        assert _detect_circular_dependencies(subtasks) is None

    def test_self_dependency(self):
        """测试自依赖"""
        subtasks = [
            SubTask(id="t1", title="任务1", description="", assigned_to="claude-code", dependencies=["t1"]),
        ]
        result = _detect_circular_dependencies(subtasks)
        assert result is not None


class TestValidateTaskDependencies:
    """任务依赖验证测试"""

    def test_valid_dependencies(self):
        """测试有效依赖"""
        subtasks = [
            SubTask(id="t1", title="任务1", description="", assigned_to="claude-code"),
            SubTask(id="t2", title="任务2", description="", assigned_to="claude-code", dependencies=["t1"]),
        ]
        warnings = _validate_task_dependencies(subtasks)
        assert len(warnings) == 0

    def test_missing_dependency(self):
        """测试缺失依赖"""
        subtasks = [
            SubTask(id="t1", title="任务1", description="", assigned_to="claude-code", dependencies=["nonexistent"]),
        ]
        warnings = _validate_task_dependencies(subtasks)
        assert len(warnings) == 1
        assert "nonexistent" in warnings[0]

    def test_self_dependency_warning(self):
        """测试自依赖警告"""
        subtasks = [
            SubTask(id="t1", title="任务1", description="", assigned_to="claude-code", dependencies=["t1"]),
        ]
        warnings = _validate_task_dependencies(subtasks)
        assert any("依赖自己" in w for w in warnings)

    def test_empty_subtasks(self):
        """测试空列表"""
        warnings = _validate_task_dependencies([])
        assert len(warnings) == 0


# ──────────────────────────────────────────────
# StudioDispatcher 测试
# ──────────────────────────────────────────────

class TestStudioDispatcherInit:
    """调度器初始化测试"""

    def test_init_success(self):
        """测试成功初始化"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        assert len(dispatcher.agents) == 1

    def test_init_empty_agents(self):
        """测试空代理字典（应警告但不报错）"""
        dispatcher = StudioDispatcher({})
        assert len(dispatcher.agents) == 0

    def test_init_non_dict_agents(self):
        """测试非字典代理"""
        with pytest.raises(TypeError, match="字典"):
            StudioDispatcher("not a dict")

    def test_init_none_agents(self):
        """测试 None 代理"""
        with pytest.raises(TypeError):
            StudioDispatcher(None)


class TestSetBroadcaster:
    """广播函数设置测试"""

    def test_set_valid_broadcaster(self):
        """测试设置有效广播函数"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        fn = AsyncMock()
        dispatcher.set_broadcaster(fn)
        assert dispatcher._broadcast == fn

    def test_set_none_broadcaster(self):
        """测试设置 None 广播函数"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        dispatcher.set_broadcaster(None)  # 不应抛出异常

    def test_set_non_callable_broadcaster(self):
        """测试设置不可调用的广播函数"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        with pytest.raises(TypeError, match="可调用"):
            dispatcher.set_broadcaster("not callable")


class TestBroadcast:
    """广播消息测试"""

    def test_broadcast_dict_message(self):
        """测试广播字典消息"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        fn = AsyncMock()
        dispatcher.set_broadcaster(fn)
        asyncio.run(dispatcher.broadcast({"type": "test"}))
        fn.assert_called_once()

    def test_broadcast_non_dict_message(self):
        """测试广播非字典消息"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        fn = AsyncMock()
        dispatcher.set_broadcaster(fn)
        asyncio.run(dispatcher.broadcast("not a dict"))
        fn.assert_not_called()

    def test_broadcast_no_broadcaster(self):
        """测试无广播函数时广播"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        # 不应抛出异常
        asyncio.run(dispatcher.broadcast({"type": "test"}))


class TestGetProject:
    """获取项目测试"""

    def test_get_existing_project(self):
        """测试获取存在的项目"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        project = Project(id="proj-1", name="测试", description="测试项目")
        dispatcher.projects["proj-1"] = project
        assert dispatcher.get_project("proj-1") == project

    def test_get_nonexistent_project(self):
        """测试获取不存在的项目"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        assert dispatcher.get_project("nonexistent") is None

    def test_get_project_invalid_id_type(self):
        """测试无效 ID 类型"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        assert dispatcher.get_project(123) is None
        assert dispatcher.get_project(None) is None


class TestStartProject:
    """启动项目测试"""

    def test_start_project_invalid_name(self):
        """测试无效项目名称"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        with pytest.raises(InvalidTaskError):
            asyncio.run(dispatcher.start_project("", "做一个网站"))

    def test_start_project_invalid_requirement(self):
        """测试无效需求"""
        agents = {"hermes": MagicMock(spec=BaseAgent)}
        dispatcher = StudioDispatcher(agents)
        with pytest.raises(InvalidTaskError):
            asyncio.run(dispatcher.start_project("项目", ""))

    def test_start_project_no_hermes(self):
        """测试无项目经理代理"""
        agents = {}
        dispatcher = StudioDispatcher(agents)
        with pytest.raises(AgentNotAvailableError):
            asyncio.run(dispatcher.start_project("项目", "做一个网站"))


class TestConstants:
    """常量测试"""

    def test_project_execution_timeout(self):
        """测试项目执行超时常量"""
        assert PROJECT_EXECUTION_TIMEOUT > 0
        assert PROJECT_EXECUTION_TIMEOUT == 600


class TestExceptionClasses:
    """异常类测试"""

    def test_dispatcher_error_hierarchy(self):
        """测试异常类层次结构"""
        assert issubclass(CircularDependencyError, DispatcherError)
        assert issubclass(MissingDependencyError, DispatcherError)
        assert issubclass(ProjectNotFoundError, DispatcherError)
        assert issubclass(ProjectTimeoutError, DispatcherError)
        assert issubclass(DispatcherError, Exception)

    def test_circular_dependency_error_message(self):
        """测试循环依赖错误消息"""
        err = CircularDependencyError("检测到循环: t1 -> t2 -> t1")
        assert "循环" in str(err)

    def test_project_timeout_error_message(self):
        """测试项目超时错误消息"""
        err = ProjectTimeoutError("项目 '测试' 执行超时 (600秒)")
        assert "超时" in str(err)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
