"""
事件路由模块测试
"""
import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from event_router import EventRouter, Event, EventType, HandlerEntry


@pytest.fixture
def root():
    """创建测试用的 Tk 根窗口"""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def canvas(root):
    """创建测试用的 Canvas"""
    canvas = tk.Canvas(root, width=100, height=100)
    canvas.pack()
    return canvas


@pytest.fixture
def router(canvas):
    """创建测试用的事件路由器"""
    return EventRouter(canvas)


# ──────────────────────────────────────────────
# EventType 测试
# ──────────────────────────────────────────────

def test_event_type_enum():
    """测试事件类型枚举包含所有类型"""
    assert EventType.CLICK.name == "CLICK"
    assert EventType.DRAG_START.name == "DRAG_START"
    assert EventType.KEY_PRESS.name == "KEY_PRESS"
    assert EventType.RIGHT_CLICK.name == "RIGHT_CLICK"
    assert EventType.HOVER_ENTER.name == "HOVER_ENTER"


# ──────────────────────────────────────────────
# Event 测试
# ──────────────────────────────────────────────

def test_event_creation():
    """测试事件对象创建"""
    event = Event(EventType.CLICK, x=50, y=50, button=1)
    assert event.type == EventType.CLICK
    assert event.x == 50
    assert event.y == 50
    assert event.button == 1


def test_event_default_values():
    """测试事件默认值"""
    event = Event(EventType.HOVER_ENTER)
    assert event.x == 0
    assert event.y == 0
    assert event.button == 0
    assert event.key == ""


def test_event_timestamp():
    """测试事件时间戳"""
    event = Event(EventType.CLICK)
    assert isinstance(event.timestamp, float)
    assert event.timestamp > 0


def test_event_stop_propagation():
    """测试事件停止传播"""
    event = Event(EventType.CLICK)
    assert event._propagation_stopped is False
    event.stop_propagation()
    assert event._propagation_stopped is True


def test_event_repr():
    """测试事件字符串表示"""
    event = Event(EventType.CLICK, x=50, y=50, button=1, key="a")
    repr_str = repr(event)
    assert "CLICK" in repr_str
    assert "50" in repr_str


# ──────────────────────────────────────────────
# HandlerEntry 测试
# ──────────────────────────────────────────────

def test_handler_entry_default_priority():
    """测试处理器条目默认优先级"""
    entry = HandlerEntry(handler=lambda e: None)
    assert entry.priority == 100


def test_handler_entry_sorting():
    """测试处理器条目排序"""
    e1 = HandlerEntry(handler=lambda e: None, priority=10)
    e2 = HandlerEntry(handler=lambda e: None, priority=50)
    e3 = HandlerEntry(handler=lambda e: None, priority=100)

    entries = [e3, e1, e2]
    entries.sort()
    assert entries[0].priority == 10
    assert entries[1].priority == 50
    assert entries[2].priority == 100


# ──────────────────────────────────────────────
# EventRouter 初始化测试
# ──────────────────────────────────────────────

def test_router_initialization(router):
    """测试路由器初始化"""
    assert router._handlers == {}
    assert router._filters == []
    assert router._dragging is False
    assert router._drag_threshold == 5
    assert router._double_click_delay == 300


def test_router_event_stats_initially_empty(router):
    """测试事件统计初始为空"""
    stats = router.get_event_stats()
    assert stats == {}


# ──────────────────────────────────────────────
# 处理器注册测试
# ──────────────────────────────────────────────

def test_router_register_handler(router):
    """测试注册事件处理器"""
    handler = MagicMock()
    router.on(EventType.CLICK, handler)

    assert EventType.CLICK in router._handlers
    assert len(router._handlers[EventType.CLICK]) == 1
    assert router._handlers[EventType.CLICK][0].handler == handler


def test_router_register_multiple_handlers(router):
    """测试注册多个处理器"""
    handler1 = MagicMock()
    handler2 = MagicMock()

    router.on(EventType.CLICK, handler1)
    router.on(EventType.CLICK, handler2)

    assert len(router._handlers[EventType.CLICK]) == 2


def test_router_register_handler_with_priority(router):
    """测试注册带优先级的处理器"""
    handler_high = MagicMock()
    handler_low = MagicMock()

    router.on(EventType.CLICK, handler_low, priority=200)
    router.on(EventType.CLICK, handler_high, priority=10)

    # 高优先级应该排在前面
    entries = router._handlers[EventType.CLICK]
    assert entries[0].handler == handler_high
    assert entries[1].handler == handler_low


def test_router_register_non_callable(router):
    """测试注册不可调用对象"""
    # 不应该抛出异常，但会记录警告
    router.on(EventType.CLICK, "not_callable")
    assert EventType.CLICK not in router._handlers


def test_router_remove_handler(router):
    """测试移除事件处理器"""
    handler = MagicMock()
    router.on(EventType.CLICK, handler)
    router.off(EventType.CLICK, handler)

    assert len(router._handlers.get(EventType.CLICK, [])) == 0


def test_router_remove_all_handlers(router):
    """测试移除所有处理器"""
    handler1 = MagicMock()
    handler2 = MagicMock()

    router.on(EventType.CLICK, handler1)
    router.on(EventType.CLICK, handler2)
    router.off(EventType.CLICK)

    assert router._handlers.get(EventType.CLICK) == []


def test_router_remove_nonexistent_handler(router):
    """测试移除不存在的处理器（不报错）"""
    handler = MagicMock()
    router.off(EventType.CLICK, handler)  # 不应抛出异常


# ──────────────────────────────────────────────
# 事件过滤器测试
# ──────────────────────────────────────────────

def test_router_add_filter(router):
    """测试添加过滤器"""
    filter_func = MagicMock(return_value=True)
    router.add_filter(filter_func)

    assert filter_func in router._filters


def test_router_add_non_callable_filter(router):
    """测试添加不可调用过滤器"""
    router.add_filter("not_callable")
    assert len(router._filters) == 0


def test_router_remove_filter(router):
    """测试移除过滤器"""
    filter_func = MagicMock(return_value=True)
    router.add_filter(filter_func)
    router.remove_filter(filter_func)

    assert filter_func not in router._filters


def test_router_remove_nonexistent_filter(router):
    """测试移除不存在的过滤器（不报错）"""
    filter_func = MagicMock(return_value=True)
    router.remove_filter(filter_func)  # 不应抛出异常


def test_router_filter_blocks_event(router):
    """测试过滤器阻止事件"""
    handler = MagicMock()
    router.on(EventType.CLICK, handler)

    # 添加返回 False 的过滤器
    router.add_filter(lambda e: False)

    event = Event(EventType.CLICK, x=50, y=50)
    router._emit(event)

    handler.assert_not_called()


def test_router_filter_passes_event(router):
    """测试过滤器允许事件通过"""
    handler = MagicMock()
    router.on(EventType.CLICK, handler)

    # 添加返回 True 的过滤器
    router.add_filter(lambda e: True)

    event = Event(EventType.CLICK, x=50, y=50)
    router._emit(event)

    handler.assert_called_once()


def test_router_filter_exception_does_not_crash(router):
    """测试过滤器异常不会崩溃"""
    def bad_filter(event):
        raise ValueError("Filter error")

    handler = MagicMock()
    router.on(EventType.CLICK, handler)
    router.add_filter(bad_filter)

    event = Event(EventType.CLICK, x=50, y=50)
    # 不应抛出异常
    router._emit(event)


# ──────────────────────────────────────────────
# 事件分发测试
# ──────────────────────────────────────────────

def test_router_emit_calls_handlers(router):
    """测试事件触发调用处理器"""
    handler = MagicMock()
    router.on(EventType.CLICK, handler)

    event = Event(EventType.CLICK, x=50, y=50)
    router._emit(event)

    handler.assert_called_once_with(event)


def test_router_emit_priority_order(router):
    """测试事件按优先级顺序分发"""
    call_order = []

    def handler_low(event):
        call_order.append("low")

    def handler_high(event):
        call_order.append("high")

    router.on(EventType.CLICK, handler_low, priority=200)
    router.on(EventType.CLICK, handler_high, priority=10)

    event = Event(EventType.CLICK, x=50, y=50)
    router._emit(event)

    assert call_order == ["high", "low"]


def test_router_emit_stop_propagation(router):
    """测试事件停止传播"""
    call_order = []

    def handler_first(event):
        call_order.append("first")
        event.stop_propagation()

    def handler_second(event):
        call_order.append("second")

    router.on(EventType.CLICK, handler_first, priority=10)
    router.on(EventType.CLICK, handler_second, priority=20)

    event = Event(EventType.CLICK, x=50, y=50)
    router._emit(event)

    assert call_order == ["first"]  # 第二个处理器不应被调用


def test_router_emit_multiple_event_types(router):
    """测试多个事件类型"""
    click_handler = MagicMock()
    drag_handler = MagicMock()

    router.on(EventType.CLICK, click_handler)
    router.on(EventType.DRAG_START, drag_handler)

    click_event = Event(EventType.CLICK, x=50, y=50)
    drag_event = Event(EventType.DRAG_START, x=10, y=10)

    router._emit(click_event)
    router._emit(drag_event)

    click_handler.assert_called_once()
    drag_handler.assert_called_once()


def test_router_emit_updates_stats(router):
    """测试事件触发更新统计"""
    event = Event(EventType.CLICK, x=50, y=50)
    router._emit(event)
    router._emit(event)

    stats = router.get_event_stats()
    assert stats["CLICK"] == 2


def test_router_reset_stats(router):
    """测试重置事件统计"""
    event = Event(EventType.CLICK, x=50, y=50)
    router._emit(event)

    router.reset_stats()
    stats = router.get_event_stats()
    assert stats == {}


# ──────────────────────────────────────────────
# 处理器异常测试
# ──────────────────────────────────────────────

def test_router_handler_exception_does_not_crash(router):
    """测试处理器异常不会崩溃"""
    def bad_handler(event):
        raise ValueError("Test error")

    router.on(EventType.CLICK, bad_handler)

    event = Event(EventType.CLICK, x=50, y=50)
    # 不应该抛出异常
    router._emit(event)


# ──────────────────────────────────────────────
# 配置测试
# ──────────────────────────────────────────────

def test_router_set_drag_threshold(router):
    """测试设置拖拽阈值"""
    router.set_drag_threshold(10)
    assert router._drag_threshold == 10


def test_router_set_drag_threshold_invalid(router):
    """测试设置无效的拖拽阈值"""
    original = router._drag_threshold
    router.set_drag_threshold(-1)
    assert router._drag_threshold == original  # 不应改变


def test_router_set_double_click_delay(router):
    """测试设置双击延迟"""
    router.set_double_click_delay(500)
    assert router._double_click_delay == 500


def test_router_set_double_click_delay_invalid(router):
    """测试设置无效的双击延迟"""
    original = router._double_click_delay
    router.set_double_click_delay(0)
    assert router._double_click_delay == original  # 不应改变


def test_router_is_dragging(router):
    """测试拖拽状态"""
    assert router.is_dragging() is False
