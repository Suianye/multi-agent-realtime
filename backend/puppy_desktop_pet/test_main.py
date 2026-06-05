"""
程序入口测试
测试新的事件路由系统集成
"""
import pytest
import tkinter as tk
from main import PuppyDesktopPet
from animations import PuppyState


def test_app_initialization():
    """测试应用初始化"""
    app = PuppyDesktopPet()
    assert app.root is not None
    assert app.pet_window is not None
    assert app.puppy is not None
    assert app.event_router is not None
    assert app.puppy_handlers is not None
    assert app.keyboard_handlers is not None
    app.root.destroy()


def test_app_start_stop():
    """测试应用启动停止"""
    app = PuppyDesktopPet()
    # 启动后立即停止（避免阻塞）
    app.root.after(100, app.stop)
    app.start()
    # 验证应用已停止
    assert not app.running


def test_app_pause_resume():
    """测试暂停恢复"""
    app = PuppyDesktopPet()
    app.running = True

    app.pause()
    assert not app.running

    app.resume()
    assert app.running
    app.root.destroy()


def test_app_get_state():
    """测试获取应用状态"""
    app = PuppyDesktopPet()
    state = app.get_state()

    assert "running" in state
    assert "puppy_state" in state
    assert "puppy_position" in state
    assert "window_position" in state
    assert "is_dragging" in state

    app.root.destroy()


def test_app_event_router_integration():
    """测试事件路由器集成"""
    try:
        app = PuppyDesktopPet()

        # 验证事件路由器已注册处理器
        from event_router import EventType
        assert EventType.CLICK in app.event_router._handlers
        assert EventType.DRAG_START in app.event_router._handlers
        assert EventType.KEY_PRESS in app.event_router._handlers

        app.root.destroy()
    except Exception as e:
        if "tk.tcl" in str(e) or "TclError" in str(e):
            pytest.skip("Tkinter 环境不可用")
        else:
            raise


def test_app_puppy_state_transitions():
    """测试小黑狗状态转换"""
    try:
        app = PuppyDesktopPet()

        # 初始状态应该是 IDLE
        assert app.puppy.get_state() == PuppyState.IDLE

        # 模拟点击事件（通过处理器）
        from event_router import Event, EventType
        event = Event(EventType.CLICK, x=50, y=50)
        app.puppy_handlers._on_click(event)

        # 应该转换到 WAGGING
        assert app.puppy.get_state() == PuppyState.WAGGING

        app.root.destroy()
    except Exception as e:
        if "tk.tcl" in str(e) or "TclError" in str(e):
            pytest.skip("Tkinter 环境不可用")
        else:
            raise
