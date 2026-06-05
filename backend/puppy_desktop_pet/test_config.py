import pytest
from config import PUPPY_SIZE, WALK_SPEED, ANIMATION_FPS, IDLE_TIMEOUT, SITTING_TIMEOUT, WAGGING_TIMEOUT

def test_config_values_exist():
    """测试配置值是否存在"""
    assert PUPPY_SIZE is not None
    assert WALK_SPEED is not None
    assert ANIMATION_FPS is not None
    assert IDLE_TIMEOUT is not None
    assert SITTING_TIMEOUT is not None
    assert WAGGING_TIMEOUT is not None

def test_config_values_are_positive():
    """测试配置值是否为正数"""
    assert PUPPY_SIZE > 0
    assert WALK_SPEED > 0
    assert ANIMATION_FPS > 0
    assert IDLE_TIMEOUT > 0
    assert SITTING_TIMEOUT > 0
    assert WAGGING_TIMEOUT > 0

def test_config_types():
    """测试配置值类型"""
    assert isinstance(PUPPY_SIZE, int)
    assert isinstance(WALK_SPEED, (int, float))
    assert isinstance(ANIMATION_FPS, int)
    assert isinstance(IDLE_TIMEOUT, int)
    assert isinstance(SITTING_TIMEOUT, int)
    assert isinstance(WAGGING_TIMEOUT, int)
