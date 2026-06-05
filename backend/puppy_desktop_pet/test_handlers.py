"""
事件处理器模块测试
"""
import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from event_router import EventRouter, Event, EventType
from handlers import (
    PuppyEventHandlers,
    WindowEventHandlers,
    KeyboardEventHandlers,
    ContextMenuHandler,
    CLICK_TRANSITIONS,
)
from animations import PuppyState


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


@pytest.fixture
def mock_puppy():
    """创建模拟的小黑狗对象"""
    puppy = MagicMock()
    puppy.get_state.return_value = PuppyState.IDLE
    puppy.get_state_message.return_value = "汪~"
    return puppy


@pytest.fixture
def mock_pet_window():
    """创建模拟的宠物窗口对象"""
    window = MagicMock()
    window.get_position.return_value = (100, 200)
    return window


@pytest.fixture
def puppy_handlers(router, mock_puppy, mock_pet_window):
    """创建测试用的小黑狗事件处理器"""
    return PuppyEventHandlers(router, mock_puppy, mock_pet_window)


# ──────────────────────────────────────────────
# 状态转换表测试
# ──────────────────────────────────────────────

def test_click_transitions_table():
    """测试状态转换表完整性"""
    # 确保所有状态都有对应的转换规则
    for state in PuppyState:
        assert state in CLICK_TRANSITIONS, f"状态 {state.name} 缺少转换规则"


def test_click_transition_idle_to_wagging():
    """测试转换规则: IDLE -> WAGGING"""
    assert CLICK_TRANSITIONS[PuppyState.IDLE] == PuppyState.WAGGING


def test_click_transition_walking_to_sitting():
    """测试转换规则: WALKING -> SITTING"""
    assert CLICK_TRANSITIONS[PuppyState.WALKING] == PuppyState.SITTING


def test_click_transition_sitting_to_wagging():
    """测试转换规则: SITTING -> WAGGING"""
    assert CLICK_TRANSITIONS[PuppyState.SITTING] == PuppyState.WAGGING


def test_click_transition_sleeping_to_yawning():
    """测试转换规则: SLEEPING -> YAWNING（睡觉时点击会醒来）"""
    assert CLICK_TRANSITIONS[PuppyState.SLEEPING] == PuppyState.YAWNING


def test_click_transition_lying_down_to_idle():
    """测试转换规则: LYING_DOWN -> IDLE（趴下时点击会站起来）"""
    assert CLICK_TRANSITIONS[PuppyState.LYING_DOWN] == PuppyState.IDLE


# ──────────────────────────────────────────────
# PuppyEventHandlers 初始化测试
# ──────────────────────────────────────────────

def test_puppy_handlers_initialization(puppy_handlers):
    """测试处理器初始化"""
    assert puppy_handlers._is_hovering is False


def test_puppy_handlers_registers_all_event_types(puppy_handlers, router):
    """测试所有事件类型都已注册"""
    expected_types = [
        EventType.CLICK,
        EventType.DOUBLE_CLICK,
        EventType.RIGHT_CLICK,
        EventType.DRAG_START,
        EventType.DRAG_MOVE,
        EventType.DRAG_END,
        EventType.HOVER_ENTER,
        EventType.HOVER_LEAVE,
    ]
    for event_type in expected_types:
        assert event_type in router._handlers, f"事件类型 {event_type.name} 未注册"


# ──────────────────────────────────────────────
# 点击事件测试
# ──────────────────────────────────────────────

def test_click_idle_to_wagging(puppy_handlers, mock_puppy):
    """测试点击: IDLE -> WAGGING"""
    mock_puppy.get_state.return_value = PuppyState.IDLE

    event = Event(EventType.CLICK, x=50, y=50)
    puppy_handlers._on_click(event)

    mock_puppy.set_state.assert_called_with(PuppyState.WAGGING)


def test_click_walking_to_sitting(puppy_handlers, mock_puppy):
    """测试点击: WALKING -> SITTING"""
    mock_puppy.get_state.return_value = PuppyState.WALKING

    event = Event(EventType.CLICK, x=50, y=50)
    puppy_handlers._on_click(event)

    mock_puppy.set_state.assert_called_with(PuppyState.SITTING)


def test_click_sitting_to_wagging(puppy_handlers, mock_puppy):
    """测试点击: SITTING -> WAGGING"""
    mock_puppy.get_state.return_value = PuppyState.SITTING

    event = Event(EventType.CLICK, x=50, y=50)
    puppy_handlers._on_click(event)

    mock_puppy.set_state.assert_called_with(PuppyState.WAGGING)


def test_click_sleeping_to_yawning(puppy_handlers, mock_puppy):
    """测试点击: SLEEPING -> YAWNING（睡觉时点击会醒来）"""
    mock_puppy.get_state.return_value = PuppyState.SLEEPING

    event = Event(EventType.CLICK, x=50, y=50)
    puppy_handlers._on_click(event)

    mock_puppy.set_state.assert_called_with(PuppyState.YAWNING)


def test_click_lying_down_to_idle(puppy_handlers, mock_puppy):
    """测试点击: LYING_DOWN -> IDLE（趴下时点击会站起来）"""
    mock_puppy.get_state.return_value = PuppyState.LYING_DOWN

    event = Event(EventType.CLICK, x=50, y=50)
    puppy_handlers._on_click(event)

    mock_puppy.set_state.assert_called_with(PuppyState.IDLE)


def test_click_shows_bubble(puppy_handlers, mock_puppy, mock_pet_window):
    """测试点击显示气泡消息"""
    event = Event(EventType.CLICK, x=50, y=50)
    puppy_handlers._on_click(event)

    mock_pet_window.show_bubble.assert_called_once()


# ──────────────────────────────────────────────
# 双击事件测试
# ──────────────────────────────────────────────

def test_double_click_to_lying_down(puppy_handlers, mock_puppy):
    """测试双击: 趴下"""
    event = Event(EventType.DOUBLE_CLICK, x=50, y=50)
    puppy_handlers._on_double_click(event)

    mock_puppy.set_state.assert_called_with(PuppyState.LYING_DOWN)


def test_double_click_shows_bubble(puppy_handlers, mock_pet_window):
    """测试双击显示气泡消息"""
    event = Event(EventType.DOUBLE_CLICK, x=50, y=50)
    puppy_handlers._on_double_click(event)

    mock_pet_window.show_bubble.assert_called_once()


# ──────────────────────────────────────────────
# 右键事件测试
# ──────────────────────────────────────────────

def test_right_click_to_yawning(puppy_handlers, mock_puppy):
    """测试右键: 打哈欠"""
    event = Event(EventType.RIGHT_CLICK, x=50, y=50)
    puppy_handlers._on_right_click(event)

    mock_puppy.set_state.assert_called_with(PuppyState.YAWNING)


def test_right_click_shows_bubble(puppy_handlers, mock_pet_window):
    """测试右键显示气泡消息"""
    event = Event(EventType.RIGHT_CLICK, x=50, y=50)
    puppy_handlers._on_right_click(event)

    mock_pet_window.show_bubble.assert_called_once()


# ──────────────────────────────────────────────
# 拖拽事件测试
# ──────────────────────────────────────────────

def test_drag_start_records_offset(puppy_handlers, mock_puppy):
    """测试拖拽开始记录偏移量"""
    event = Event(EventType.DRAG_START, x=10, y=20)
    puppy_handlers._on_drag_start(event)

    assert puppy_handlers._drag_offset_x == 10
    assert puppy_handlers._drag_offset_y == 20


def test_drag_start_sets_idle(puppy_handlers, mock_puppy):
    """测试拖拽开始时小黑狗回到空闲状态"""
    event = Event(EventType.DRAG_START, x=10, y=10)
    puppy_handlers._on_drag_start(event)

    mock_puppy.set_state.assert_called_with(PuppyState.IDLE)


def test_drag_move_updates_window_position(puppy_handlers, mock_pet_window):
    """测试拖拽移动更新窗口位置"""
    # 设置初始偏移量
    puppy_handlers._drag_offset_x = 50
    puppy_handlers._drag_offset_y = 50

    event = Event(EventType.DRAG_MOVE, x=150, y=250)
    puppy_handlers._on_drag_move(event)

    # 新位置 = 窗口原位置 + (鼠标位置 - 偏移量)
    # (100 + 150 - 50, 200 + 250 - 50) = (200, 400)
    mock_pet_window.set_position.assert_called_with(200, 400)


def test_drag_end(puppy_handlers):
    """测试拖拽结束"""
    event = Event(EventType.DRAG_END, x=100, y=100)
    # 不应抛出异常
    puppy_handlers._on_drag_end(event)


# ──────────────────────────────────────────────
# 悬停事件测试
# ──────────────────────────────────────────────

def test_hover_enter(puppy_handlers):
    """测试鼠标进入"""
    event = Event(EventType.HOVER_ENTER, x=50, y=50)
    puppy_handlers._on_hover_enter(event)

    assert puppy_handlers.is_hovering() is True


def test_hover_leave(puppy_handlers):
    """测试鼠标离开"""
    # 先进入
    puppy_handlers._is_hovering = True

    event = Event(EventType.HOVER_LEAVE)
    puppy_handlers._on_hover_leave(event)

    assert puppy_handlers.is_hovering() is False


# ──────────────────────────────────────────────
# 拖拽过滤器测试
# ──────────────────────────────────────────────

def test_drag_filter_blocks_click_when_dragging(puppy_handlers, router):
    """测试拖拽时阻止点击"""
    router._dragging = True

    click_event = Event(EventType.CLICK, x=50, y=50)
    result = puppy_handlers._drag_filter(click_event)

    assert result is False


def test_drag_filter_passes_click_when_not_dragging(puppy_handlers, router):
    """测试非拖拽时允许点击"""
    router._dragging = False

    click_event = Event(EventType.CLICK, x=50, y=50)
    result = puppy_handlers._drag_filter(click_event)

    assert result is True


def test_drag_filter_passes_other_events(puppy_handlers, router):
    """测试过滤器允许其他事件通过"""
    router._dragging = True

    drag_event = Event(EventType.DRAG_START, x=10, y=10)
    result = puppy_handlers._drag_filter(drag_event)

    assert result is True


# ──────────────────────────────────────────────
# WindowEventHandlers 测试
# ──────────────────────────────────────────────

@pytest.fixture
def mock_root():
    """创建模拟的根窗口"""
    root = MagicMock()
    root.protocol = MagicMock()
    return root


@pytest.fixture
def window_handlers(mock_root, mock_pet_window):
    """创建测试用的窗口事件处理器"""
    return WindowEventHandlers(mock_root, mock_pet_window)


def test_window_handlers_initialization(window_handlers, mock_root):
    """测试窗口处理器初始化"""
    mock_root.protocol.assert_called_with("WM_DELETE_WINDOW", window_handlers._on_close)


def test_window_close(window_handlers, mock_root):
    """测试窗口关闭"""
    window_handlers._on_close()

    mock_root.quit.assert_called_once()
    mock_root.destroy.assert_called_once()


def test_window_close_with_callback(window_handlers, mock_root):
    """测试窗口关闭时调用回调"""
    callback = MagicMock()
    window_handlers.on_close(callback)

    window_handlers._on_close()

    callback.assert_called_once()


def test_window_close_callback_exception(mock_root, mock_pet_window):
    """测试窗口关闭回调异常不会崩溃"""
    window_handlers = WindowEventHandlers(mock_root, mock_pet_window)

    def bad_callback():
        raise ValueError("Callback error")

    window_handlers.on_close(bad_callback)

    # 不应抛出异常
    window_handlers._on_close()


# ──────────────────────────────────────────────
# KeyboardEventHandlers 测试
# ──────────────────────────────────────────────

@pytest.fixture
def mock_app():
    """创建模拟的应用对象"""
    app = MagicMock()
    app.running = False
    app.puppy = MagicMock()
    return app


@pytest.fixture
def keyboard_handlers(router, mock_app):
    """创建测试用的键盘事件处理器"""
    return KeyboardEventHandlers(router, mock_app)


def test_keyboard_quit(keyboard_handlers, mock_app):
    """测试键盘退出"""
    keyboard_handlers._quit()

    mock_app.stop.assert_called_once()


def test_keyboard_pause(keyboard_handlers, mock_app):
    """测试键盘暂停"""
    keyboard_handlers._pause()

    mock_app.pause.assert_called_once()


def test_keyboard_resume(keyboard_handlers, mock_app):
    """测试键盘恢复"""
    keyboard_handlers._resume()

    mock_app.resume.assert_called_once()


def test_keyboard_sit(keyboard_handlers, mock_app):
    """测试键盘坐下"""
    keyboard_handlers._sit()

    mock_app.puppy.set_state.assert_called_with(PuppyState.SITTING)


def test_keyboard_walk(keyboard_handlers, mock_app):
    """测试键盘走动"""
    keyboard_handlers._walk()

    mock_app.puppy.set_state.assert_called_with(PuppyState.WALKING)


def test_keyboard_interact(keyboard_handlers, mock_app):
    """测试键盘互动"""
    keyboard_handlers._interact()

    mock_app.puppy.on_click.assert_called_once()


def test_keyboard_key_press_registered(router, keyboard_handlers):
    """测试键盘事件已注册"""
    assert EventType.KEY_PRESS in router._handlers


def test_keyboard_bind_custom_key(keyboard_handlers, router):
    """测试绑定自定义快捷键"""
    custom_handler = MagicMock()
    keyboard_handlers.bind_key("x", custom_handler)

    # 触发 x 键
    event = Event(EventType.KEY_PRESS, key="x")
    keyboard_handlers._on_key_press(event)

    custom_handler.assert_called_once()


def test_keyboard_unbind_key(keyboard_handlers):
    """测试解绑快捷键"""
    custom_handler = MagicMock()
    keyboard_handlers.bind_key("x", custom_handler)
    keyboard_handlers.unbind_key("x")

    # 触发 x 键（不应调用）
    event = Event(EventType.KEY_PRESS, key="x")
    keyboard_handlers._on_key_press(event)

    custom_handler.assert_not_called()


def test_keyboard_bind_non_callable(keyboard_handlers):
    """测试绑定不可调用对象"""
    # 不应抛出异常
    keyboard_handlers.bind_key("x", "not_callable")


def test_keyboard_bind_empty_key(keyboard_handlers):
    """测试绑定空按键"""
    handler = MagicMock()
    keyboard_handlers.bind_key("", handler)
    # 不应抛出异常


# ──────────────────────────────────────────────
# ContextMenuHandler 测试
# ──────────────────────────────────────────────

@pytest.fixture
def context_menu_handler(router, mock_pet_window, mock_puppy, mock_app):
    """创建测试用的上下文菜单处理器"""
    # 需要提供一个真实的窗口给 tk.Menu
    window = MagicMock()
    mock_pet_window.get_window.return_value = window
    return ContextMenuHandler(router, mock_pet_window, mock_puppy, mock_app)


def test_context_menu_handler_initialization(context_menu_handler, router):
    """测试上下文菜单处理器初始化"""
    assert EventType.RIGHT_CLICK in router._handlers


def test_context_menu_handler_registered(router, mock_pet_window, mock_puppy, mock_app):
    """测试上下文菜单处理器已注册"""
    window = MagicMock()
    mock_pet_window.get_window.return_value = window
    ContextMenuHandler(router, mock_pet_window, mock_puppy, mock_app)

    # 右键事件应该有多个处理器
    right_click_handlers = router._handlers.get(EventType.RIGHT_CLICK, [])
    assert len(right_click_handlers) >= 1
