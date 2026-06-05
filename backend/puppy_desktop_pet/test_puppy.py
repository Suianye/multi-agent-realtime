"""
小黑狗核心逻辑测试
"""
import pytest
import tkinter as tk
from puppy import Puppy
from animations import PuppyState


@pytest.fixture
def root():
    """创建 tkinter 根窗口"""
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def puppy(root):
    """创建小黑狗实例"""
    canvas = tk.Canvas(root, width=100, height=120)
    canvas.pack()
    return Puppy(canvas)


def test_puppy_initialization(puppy):
    """测试小黑狗初始化"""
    assert puppy.state == PuppyState.IDLE
    assert puppy.x == 50
    assert puppy.y == 60


def test_puppy_on_click_idle(puppy):
    """测试空闲状态点击"""
    puppy.state = PuppyState.IDLE
    puppy.on_click()
    assert puppy.state == PuppyState.WAGGING


def test_puppy_on_click_walking(puppy):
    """测试走路状态点击"""
    puppy.state = PuppyState.WALKING
    puppy.on_click()
    assert puppy.state == PuppyState.SITTING


def test_puppy_on_click_sitting(puppy):
    """测试坐下状态点击"""
    puppy.state = PuppyState.SITTING
    puppy.on_click()
    assert puppy.state == PuppyState.IDLE


def test_puppy_update(puppy):
    """测试更新函数"""
    puppy.update()
    # 验证更新后状态可能变化（取决于超时）
    assert puppy.state in [PuppyState.IDLE, PuppyState.WALKING, PuppyState.SITTING, PuppyState.WAGGING]


def test_puppy_move(puppy):
    """测试移动函数"""
    initial_x = puppy.x
    puppy.direction = 1  # 向右
    puppy._move()
    assert puppy.x > initial_x


def test_puppy_boundary_check(puppy):
    """测试边界检测"""
    puppy.x = 10  # 接近左边界
    puppy.direction = -1  # 向左
    puppy._check_boundary()
    assert puppy.direction == 1  # 应该转向


def test_get_state(puppy):
    """测试获取状态"""
    assert puppy.get_state() == PuppyState.IDLE


def test_get_position(puppy):
    """测试获取位置"""
    pos = puppy.get_position()
    assert isinstance(pos, tuple)
    assert len(pos) == 2
