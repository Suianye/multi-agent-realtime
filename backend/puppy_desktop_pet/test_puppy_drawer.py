import pytest
import tkinter as tk
from puppy_drawer import PuppyDrawer
from animations import PuppyState


@pytest.fixture(scope="session")
def root():
    """创建 tkinter 根窗口（整个测试会话共享）"""
    _root = tk.Tk()
    _root.withdraw()  # 隐藏窗口
    yield _root
    _root.destroy()


@pytest.fixture
def canvas(root):
    """创建测试用 Canvas"""
    _canvas = tk.Canvas(root, width=100, height=120)
    _canvas.pack()
    yield _canvas
    _canvas.delete("all")
    _canvas.destroy()


def test_drawer_initialization(canvas):
    """测试绘制器初始化"""
    drawer = PuppyDrawer(canvas)
    assert drawer.canvas == canvas
    assert drawer.center_x == 60
    assert drawer.center_y == 70


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
    drawer.update_animation(PuppyState.WALKING)
    # 更新后应该有绘制对象
    assert len(canvas.find_all()) > 0


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
