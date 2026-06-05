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


def test_get_canvas(root):
    """测试获取 Canvas"""
    window = PetWindow(root)
    canvas = window.get_canvas()
    assert canvas is not None
    assert isinstance(canvas, tk.Canvas)
