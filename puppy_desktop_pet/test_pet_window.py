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


def test_pet_window_drag_move_no_accumulation(root):
    """测试拖拽移动不会累积偏移（修复累积 bug）"""
    window = PetWindow(root)
    window.set_position(100, 200)

    # 模拟拖拽开始
    start_event = type('Event', (), {'x': 50, 'y': 50})()
    window._on_drag_start(start_event)

    # 模拟连续两次小幅移动
    move1 = type('Event', (), {'x': 55, 'y': 55})()
    window._on_drag_move(move1)
    assert window.x == 105, f"Expected 105, got {window.x}"
    assert window.y == 205, f"Expected 205, got {window.y}"

    move2 = type('Event', (), {'x': 60, 'y': 60})()
    window._on_drag_move(move2)
    # 累积 bug 会导致 x=120, y=220；正确应为 x=110, y=210
    assert window.x == 110, f"Expected 110, got {window.x} (accumulation bug!)"
    assert window.y == 210, f"Expected 210, got {window.y} (accumulation bug!)"


def test_get_position(root):
    """测试获取位置"""
    window = PetWindow(root)
    window.set_position(300, 400)
    assert window.get_position() == (300, 400)
