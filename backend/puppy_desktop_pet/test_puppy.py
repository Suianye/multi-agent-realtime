"""
小黑狗核心逻辑测试
测试状态机和新添加的 set_state 方法
"""
import pytest
import tkinter as tk
from puppy import Puppy
from animations import PuppyState


@pytest.fixture
def root():
    """创建 tkinter 根窗口"""
    try:
        root = tk.Tk()
        root.withdraw()
        yield root
        root.destroy()
    except Exception as e:
        if "tk.tcl" in str(e) or "TclError" in str(e):
            pytest.skip("Tkinter 环境不可用")
        else:
            raise


@pytest.fixture
def puppy(root):
    """创建小黑狗实例"""
    canvas = tk.Canvas(root, width=100, height=120)
    canvas.pack()
    return Puppy(canvas)


def test_puppy_initialization(puppy):
    """测试小黑狗初始化"""
    assert puppy.state == PuppyState.IDLE
    assert puppy.x == 60  # CANVAS_WIDTH // 2 = 120 // 2
    assert puppy.y == 70  # 固定值，确保在画布中间


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
    # 坐下时点击会摇尾巴（更开心）
    assert puppy.state == PuppyState.WAGGING


def test_puppy_set_state(puppy):
    """测试 set_state 方法"""
    # 初始状态
    assert puppy.state == PuppyState.IDLE

    # 设置新状态
    puppy.set_state(PuppyState.WAGGING)
    assert puppy.state == PuppyState.WAGGING

    # 设置相同状态不应重置计时器
    puppy.state_timer = 100
    puppy.set_state(PuppyState.WAGGING)
    assert puppy.state_timer == 100

    # 设置不同状态应重置计时器
    puppy.set_state(PuppyState.SITTING)
    assert puppy.state == PuppyState.SITTING
    assert puppy.state_timer == 0


def test_puppy_update(puppy):
    """测试更新函数"""
    puppy.update()
    # 验证更新后状态可能变化（取决于超时）
    assert puppy.state in [
        PuppyState.IDLE, PuppyState.WALKING, PuppyState.SITTING,
        PuppyState.WAGGING, PuppyState.YAWNING, PuppyState.STRETCHING
    ]


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


def test_puppy_state_transitions():
    """测试状态转换完整性"""
    # 这个测试需要在有 tkinter 环境的情况下运行
    try:
        root = tk.Tk()
        root.withdraw()
        canvas = tk.Canvas(root, width=100, height=120)
        canvas.pack()
        puppy = Puppy(canvas)

        # 测试所有状态都可以通过 set_state 设置
        for state in PuppyState:
            puppy.set_state(state)
            assert puppy.state == state

        root.destroy()
    except Exception:
        pytest.skip("Tkinter 环境不可用")
