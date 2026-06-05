import pytest
import tkinter as tk
from puppy_drawer import PuppyDrawer
from animations import PuppyState


@pytest.fixture
def root():
    """创建 tkinter 根窗口"""
    root = tk.Tk()
    root.withdraw()  # 隐藏窗口
    yield root
    root.destroy()


@pytest.fixture
def canvas(root):
    """创建测试用 Canvas"""
    canvas = tk.Canvas(root, width=100, height=120)
    canvas.pack()
    return canvas


def test_drawer_initialization(canvas):
    """测试绘制器初始化"""
    drawer = PuppyDrawer(canvas)
    assert drawer.canvas == canvas
    assert drawer.center_x == 50
    assert drawer.center_y == 60


def test_draw_puppy(canvas):
    """测试绘制小黑狗"""
    drawer = PuppyDrawer(canvas)
    drawer.draw_puppy(PuppyState.IDLE)
    # 验证 Canvas 上有对象
    assert len(canvas.find_all()) > 0


def test_clear_puppy(canvas):
    """测试清除小黑狗"""
    drawer = PuppyDrawer(canvas)
    drawer.draw_puppy(PuppyState.IDLE)
    drawer.clear_puppy()
    assert len(canvas.find_all()) == 0


def test_update_animation(canvas):
    """测试更新动画"""
    drawer = PuppyDrawer(canvas)
    drawer.draw_puppy(PuppyState.IDLE)
    initial_items = len(canvas.find_all())
    drawer.update_animation(PuppyState.WALKING)
    # 更新后应该有相同数量的对象（只是位置变化）
    assert len(canvas.find_all()) == initial_items


def test_set_position(canvas):
    """测试设置绘制位置"""
    drawer = PuppyDrawer(canvas)
    drawer.set_position(30, 40)
    assert drawer.center_x == 30
    assert drawer.center_y == 40


def test_draw_all_states(canvas):
    """测试绘制所有状态"""
    drawer = PuppyDrawer(canvas)
    for state in PuppyState:
        drawer.draw_puppy(state)
        assert len(canvas.find_all()) > 0
