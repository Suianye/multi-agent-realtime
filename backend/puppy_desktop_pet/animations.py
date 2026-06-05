"""
动画帧管理模块
定义小黑狗各个状态的动画帧
"""
from enum import Enum
from typing import Dict, List, Tuple


class PuppyState(Enum):
    """小黑狗状态枚举"""
    IDLE = "idle"
    WALKING = "walking"
    SITTING = "sitting"
    WAGGING = "wagging"


# 动画帧定义：每个状态包含多帧，每帧定义各部件的相对位置
# 格式：{部件名: (x偏移, y偏移, 宽度, 高度, 角度)}
ANIMATION_FRAMES = {
    PuppyState.IDLE: [
        {
            "head": (0, -20, 30, 25, 0),
            "body": (0, 0, 40, 30, 0),
            "legs": [(-15, 15, 8, 20, 0), (15, 15, 8, 20, 0),
                     (-15, 15, 8, 20, 0), (15, 15, 8, 20, 0)],
            "tail": (20, -5, 15, 5, -30),
            "nose": (15, -15, 5, 5, 0),
            "eyes": [(-5, -18, 4, 4, 0), (5, -18, 4, 4, 0)]
        }
    ],
    PuppyState.WALKING: [
        {
            "head": (0, -20, 30, 25, 0),
            "body": (0, 0, 40, 30, 0),
            "legs": [(-15, 15, 8, 20, -10), (15, 15, 8, 20, 10),
                     (-15, 15, 8, 20, 10), (15, 15, 8, 20, -10)],
            "tail": (20, -5, 15, 5, -20),
            "nose": (15, -15, 5, 5, 0),
            "eyes": [(-5, -18, 4, 4, 0), (5, -18, 4, 4, 0)]
        },
        {
            "head": (0, -20, 30, 25, 0),
            "body": (0, -2, 40, 30, 0),
            "legs": [(-15, 15, 8, 20, 10), (15, 15, 8, 20, -10),
                     (-15, 15, 8, 20, -10), (15, 15, 8, 20, 10)],
            "tail": (20, -7, 15, 5, -40),
            "nose": (15, -17, 5, 5, 0),
            "eyes": [(-5, -20, 4, 4, 0), (5, -20, 4, 4, 0)]
        }
    ],
    PuppyState.SITTING: [
        {
            "head": (0, -15, 30, 25, 0),
            "body": (0, 5, 40, 25, 0),
            "legs": [(-15, 20, 8, 15, 0), (15, 20, 8, 15, 0),
                     (-15, 20, 8, 15, 30), (15, 20, 8, 15, -30)],
            "tail": (20, 0, 15, 5, -10),
            "nose": (15, -10, 5, 5, 0),
            "eyes": [(-5, -13, 4, 4, 0), (5, -13, 4, 4, 0)]
        }
    ],
    PuppyState.WAGGING: [
        {
            "head": (0, -20, 30, 25, 0),
            "body": (0, 0, 40, 30, 0),
            "legs": [(-15, 15, 8, 20, 0), (15, 15, 8, 20, 0),
                     (-15, 15, 8, 20, 0), (15, 15, 8, 20, 0)],
            "tail": (20, -5, 15, 5, -45),
            "nose": (15, -15, 5, 5, 0),
            "eyes": [(-5, -18, 4, 4, 0), (5, -18, 4, 4, 0)]
        },
        {
            "head": (0, -20, 30, 25, 0),
            "body": (0, 0, 40, 30, 0),
            "legs": [(-15, 15, 8, 20, 0), (15, 15, 8, 20, 0),
                     (-15, 15, 8, 20, 0), (15, 15, 8, 20, 0)],
            "tail": (20, -5, 15, 5, -15),
            "nose": (15, -15, 5, 5, 0),
            "eyes": [(-5, -18, 4, 4, 0), (5, -18, 4, 4, 0)]
        }
    ]
}


class AnimationManager:
    """动画管理器"""

    def __init__(self):
        self.current_state = PuppyState.IDLE
        self.current_frame = 0
        self.frames = ANIMATION_FRAMES

    def get_current_frame(self) -> Dict:
        """获取当前帧数据"""
        state_frames = self.frames[self.current_state]
        return state_frames[self.current_frame % len(state_frames)]

    def advance_frame(self):
        """推进到下一帧"""
        state_frames = self.frames[self.current_state]
        self.current_frame = (self.current_frame + 1) % len(state_frames)

    def set_state(self, state: PuppyState):
        """设置状态"""
        if self.current_state != state:
            self.current_state = state
            self.current_frame = 0

    def get_state(self) -> PuppyState:
        """获取当前状态"""
        return self.current_state
