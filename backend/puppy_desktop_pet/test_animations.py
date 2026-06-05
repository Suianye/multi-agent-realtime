import pytest
from animations import AnimationManager, PuppyState

def test_puppy_state_enum():
    """测试状态枚举定义"""
    assert PuppyState.IDLE.value == "idle"
    assert PuppyState.WALKING.value == "walking"
    assert PuppyState.SITTING.value == "sitting"
    assert PuppyState.WAGGING.value == "wagging"

def test_animation_manager_initialization():
    """测试动画管理器初始化"""
    manager = AnimationManager()
    assert manager.current_state == PuppyState.IDLE
    assert manager.current_frame == 0

def test_get_frame_returns_dict():
    """测试获取帧返回字典"""
    manager = AnimationManager()
    frame = manager.get_current_frame()
    assert isinstance(frame, dict)
    assert "head" in frame
    assert "body" in frame
    assert "legs" in frame
    assert "tail" in frame

def test_advance_frame():
    """测试帧推进"""
    manager = AnimationManager()
    # 切换到有多帧的状态进行测试
    manager.set_state(PuppyState.WALKING)
    initial_frame = manager.current_frame
    manager.advance_frame()
    assert manager.current_frame != initial_frame

def test_set_state():
    """测试状态切换"""
    manager = AnimationManager()
    manager.set_state(PuppyState.WALKING)
    assert manager.current_state == PuppyState.WALKING
    assert manager.current_frame == 0
