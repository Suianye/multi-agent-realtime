import pytest
from config import (
    PUPPY_SIZE, WALK_SPEED, ANIMATION_FPS, IDLE_TIMEOUT, SITTING_TIMEOUT, WAGGING_TIMEOUT,
    COLOR_BLACK, COLOR_WHITE, COLOR_PINK, COLOR_DARK_GRAY,
    WINDOW_TITLE, CANVAS_WIDTH, CANVAS_HEIGHT,
)

ALL_COLORS = [COLOR_BLACK, COLOR_WHITE, COLOR_PINK, COLOR_DARK_GRAY]

def test_config_values_exist():
    """测试配置值是否存在"""
    assert PUPPY_SIZE is not None
    assert WALK_SPEED is not None
    assert ANIMATION_FPS is not None
    assert IDLE_TIMEOUT is not None
    assert SITTING_TIMEOUT is not None
    assert WAGGING_TIMEOUT is not None
    assert COLOR_BLACK is not None
    assert COLOR_WHITE is not None
    assert COLOR_PINK is not None
    assert COLOR_DARK_GRAY is not None
    assert WINDOW_TITLE is not None
    assert CANVAS_WIDTH is not None
    assert CANVAS_HEIGHT is not None

def test_config_values_are_positive():
    """测试配置值是否为正数"""
    assert PUPPY_SIZE > 0
    assert WALK_SPEED > 0
    assert ANIMATION_FPS > 0
    assert IDLE_TIMEOUT > 0
    assert SITTING_TIMEOUT > 0
    assert WAGGING_TIMEOUT > 0
    assert CANVAS_WIDTH > 0
    assert CANVAS_HEIGHT > 0

def test_config_types():
    """测试配置值类型"""
    assert isinstance(PUPPY_SIZE, int)
    assert isinstance(WALK_SPEED, (int, float))
    assert isinstance(ANIMATION_FPS, int)
    assert isinstance(IDLE_TIMEOUT, int)
    assert isinstance(SITTING_TIMEOUT, int)
    assert isinstance(WAGGING_TIMEOUT, int)
    assert isinstance(COLOR_BLACK, str)
    assert isinstance(COLOR_WHITE, str)
    assert isinstance(COLOR_PINK, str)
    assert isinstance(COLOR_DARK_GRAY, str)
    assert isinstance(WINDOW_TITLE, str)
    assert isinstance(CANVAS_WIDTH, int)
    assert isinstance(CANVAS_HEIGHT, int)

def test_color_values():
    """测试颜色值格式"""
    for color in ALL_COLORS:
        assert isinstance(color, str), f"{color} 应为字符串"
        assert color.startswith("#"), f"{color} 应以 # 开头"
        assert len(color) == 7, f"{color} 长度应为 7"

def test_window_config():
    """测试窗口配置"""
    assert isinstance(WINDOW_TITLE, str)
    assert len(WINDOW_TITLE) > 0
    assert isinstance(CANVAS_WIDTH, int)
    assert isinstance(CANVAS_HEIGHT, int)
    assert CANVAS_WIDTH > 0
    assert CANVAS_HEIGHT > 0
