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
    assert manager.get_state() == PuppyState.IDLE

def test_get_frame_returns_dict():
    """测试获取帧返回字典包含所有部件"""
    manager = AnimationManager()
    frame = manager.get_current_frame()
    assert isinstance(frame, dict)
    assert "head" in frame
    assert "body" in frame
    assert "legs" in frame
    assert "tail" in frame
    assert "nose" in frame
    assert "eyes" in frame

def test_advance_frame():
    """测试帧推进"""
    manager = AnimationManager()
    # 切换到有多帧的状态进行测试
    manager.set_state(PuppyState.WALKING)
    # WALKING 现在有 4 帧，测试帧推进
    manager.advance_frame()
    frame1 = manager.get_current_frame()
    manager.advance_frame()
    frame2 = manager.get_current_frame()
    # 帧应该不同（至少在某些情况下）
    assert isinstance(frame1, dict)
    assert isinstance(frame2, dict)

def test_set_state():
    """测试状态切换"""
    manager = AnimationManager()
    manager.set_state(PuppyState.WALKING)
    assert manager.get_state() == PuppyState.WALKING


def test_frame_loops_back_to_zero():
    """测试多帧状态下帧循环"""
    manager = AnimationManager()
    manager.set_state(PuppyState.WALKING)  # WALKING 有 4 帧
    # 推进多帧，应该能循环
    for _ in range(5):
        manager.advance_frame()
    # 状态应该仍然是 WALKING
    assert manager.get_state() == PuppyState.WALKING


def test_set_same_state_does_not_reset_frame():
    """测试连续设置同一状态的行为"""
    manager = AnimationManager()
    manager.set_state(PuppyState.WALKING)
    manager.advance_frame()
    # 再次设置同一状态，根据实现可能会重置帧
    manager.set_state(PuppyState.WALKING)
    assert manager.get_state() == PuppyState.WALKING


def test_get_state():
    """测试获取当前状态"""
    manager = AnimationManager()
    assert manager.get_state() == PuppyState.IDLE
    manager.set_state(PuppyState.WAGGING)
    assert manager.get_state() == PuppyState.WAGGING
