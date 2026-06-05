"""
窗口管理模块测试
"""
import pytest
import tkinter as tk
from pet_window import PetWindow


@pytest.fixture
def root():
    """创建 tkinter 根窗口"""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


def test_pet_window_initialization(root):
    """测试窗口初始化"""
    window = PetWindow(root)
    assert window.window is not None
    assert window.canvas is not None


def test_pet_window_position(root):
    """测试窗口位置设置"""
    window = PetWindow(root)
    window.set_position(100, 200)
    # 验证位置已设置（实际值可能因系统而异）
    assert window.x == 100
    assert window.y == 200


def test_pet_window_drag_start(root):
    """测试拖拽开始"""
    window = PetWindow(root)
    event = type('Event', (), {'x': 10, 'y': 10})()
    window._on_drag_start(event)
    assert window.dragging == True


def test_pet_window_drag_end(root):
    """测试拖拽结束"""
    window = PetWindow(root)
    window.dragging = True
    window._on_drag_end(None)
    assert window.dragging == False


def test_get_position(root):
    """测试获取位置"""
    window = PetWindow(root)
    window.set_position(50, 75)
    assert window.get_position() == (50, 75)


def test_pet_window_drag_move(root):
    """测试拖拽移动"""
    window = PetWindow(root)
    # 使用安全起始位置（考虑边界保护 margin=15）
    window.set_position(100, 100)

    # 模拟拖拽开始
    event_start = type('Event', (), {'x': 10, 'y': 10})()
    window._on_drag_start(event_start)

    # 模拟拖拽移动
    event_move = type('Event', (), {'x': 15, 'y': 10})()
    window._on_drag_move(event_move)

    # 验证位置更新（拖拽偏移 = 15-10=5）
    assert window.x == 105
    assert window.y == 100

    # 再次移动
    event_move2 = type('Event', (), {'x': 20, 'y': 10})()
    window._on_drag_move(event_move2)

    # 验证位置正确累加（不应该有累积偏移）
    assert window.x == 110
    assert window.y == 100


def test_get_canvas(root):
    """测试获取 Canvas"""
    window = PetWindow(root)
    canvas = window.get_canvas()
    assert canvas is not None
    assert isinstance(canvas, tk.Canvas)


def test_show_hide_bubble(root):
    """测试气泡显示和隐藏"""
    window = PetWindow(root)
    window.show_bubble("测试消息")
    assert window.bubble_visible == True
    window.hide_bubble()
    assert window.bubble_visible == False


def test_destroy_window(root):
    """测试窗口销毁"""
    window = PetWindow(root)
    assert not window.is_destroyed()
    window.destroy()
    assert window.is_destroyed()


def test_operations_after_destroy(root):
    """测试销毁后的操作"""
    window = PetWindow(root)
    window.destroy()
    # 销毁后调用方法不应抛出异常
    window.set_position(100, 100)
    window.show_bubble("test")
    window.hide_bubble()
