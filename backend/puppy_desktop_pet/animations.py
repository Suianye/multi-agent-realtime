"""
动画帧管理模块
定义小黑狗各个状态的动画帧
"""
from enum import Enum
from typing import Dict, List, Tuple


class PuppyState(Enum):
    """小黑狗状态枚举"""
    IDLE = "idle"           # 站立
    WALKING = "walking"     # 走路
    SITTING = "sitting"     # 坐下
    WAGGING = "wagging"     # 摇尾巴
    YAWNING = "yawning"     # 打哈欠
    STRETCHING = "stretching"  # 伸懒腰
    SLEEPING = "sleeping"   # 睡觉
    LYING_DOWN = "lying_down"  # 趴下


# 动画帧定义：每个状态包含多帧，每帧定义各部件的相对位置
# 格式：{部件名: (x偏移, y偏移, 宽度, 高度, 角度)}
ANIMATION_FRAMES = {
    PuppyState.IDLE: [
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -30),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 5, 0), (6, -22, 5, 5, 0)],
            "tongue": None
        }
    ],
    PuppyState.WALKING: [
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, -12), (16, 18, 9, 22, 12),
                     (-16, 18, 9, 22, 12), (16, 18, 9, 22, -12)],
            "tail": (22, -8, 18, 6, -20),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 5, 0), (6, -22, 5, 5, 0)],
            "tongue": None
        },
        {
            "head": (0, -27, 34, 28, 0),
            "body": (0, -2, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 12), (16, 18, 9, 22, -12),
                     (-16, 18, 9, 22, -12), (16, 18, 9, 22, 12)],
            "tail": (22, -10, 18, 6, -45),
            "nose": (17, -22, 6, 5, 0),
            "eyes": [(-6, -24, 5, 5, 0), (6, -24, 5, 5, 0)],
            "tongue": (12, -14, 5, 8, 0)
        }
    ],
    PuppyState.SITTING: [
        {
            "head": (0, -18, 34, 28, 0),
            "body": (0, 5, 44, 28, 0),
            "legs": [(-16, 22, 9, 16, 0), (16, 22, 9, 16, 0),
                     (-16, 22, 9, 16, 35), (16, 22, 9, 16, -35)],
            "tail": (22, -2, 18, 6, -10),
            "nose": (17, -13, 6, 5, 0),
            "eyes": [(-6, -16, 5, 5, 0), (6, -16, 5, 5, 0)],
            "tongue": None
        }
    ],
    PuppyState.WAGGING: [
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -50),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 6, 0), (6, -22, 5, 6, 0)],
            "tongue": (12, -15, 5, 10, 0)
        },
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -10),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 6, 0), (6, -22, 5, 6, 0)],
            "tongue": (12, -15, 5, 10, 0)
        }
    ],
    PuppyState.YAWNING: [
        {
            "head": (0, -22, 34, 30, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -20),
            "nose": (17, -17, 6, 5, 0),
            "eyes": [(-6, -20, 5, 2, 0), (6, -20, 5, 2, 0)],
            "mouth": (10, -12, 10, 10, 0),
            "tongue": None
        },
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -20),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 2, 0), (6, -22, 5, 2, 0)],
            "mouth": (12, -14, 8, 8, 0),
            "tongue": None
        }
    ],
    PuppyState.STRETCHING: [
        {
            "head": (15, -20, 34, 28, 10),
            "body": (5, 2, 50, 28, 5),
            "legs": [(-20, 16, 9, 25, -15), (20, 16, 9, 25, 15),
                     (-20, 16, 9, 25, -10), (20, 16, 9, 25, 10)],
            "tail": (28, -5, 20, 6, -30),
            "nose": (32, -15, 6, 5, 0),
            "eyes": [(-3, -18, 5, 3, 0), (9, -18, 5, 3, 0)],
            "tongue": None
        },
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -40),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 4, 0), (6, -22, 5, 4, 0)],
            "tongue": (12, -15, 5, 8, 0)
        }
    ],
    PuppyState.SLEEPING: [
        {
            "head": (0, -15, 34, 25, -15),
            "body": (0, 5, 48, 28, 0),
            "legs": [(-18, 20, 10, 18, -5), (18, 20, 10, 18, 5),
                     (-18, 20, 10, 18, -5), (18, 20, 10, 18, 5)],
            "tail": (24, 2, 18, 6, -15),
            "nose": (12, -10, 6, 5, 0),
            "eyes": [(-8, -13, 6, 1, 0), (2, -13, 6, 1, 0)],
            "zzz": (20, -30, 15, 15, 0),
            "tongue": None
        },
        {
            "head": (0, -15, 34, 25, -15),
            "body": (0, 5, 48, 28, 0),
            "legs": [(-18, 20, 10, 18, -5), (18, 20, 10, 18, 5),
                     (-18, 20, 10, 18, -5), (18, 20, 10, 18, 5)],
            "tail": (24, 2, 18, 6, -15),
            "nose": (12, -10, 6, 5, 0),
            "eyes": [(-8, -13, 6, 1, 0), (2, -13, 6, 1, 0)],
            "zzz": (25, -35, 12, 12, 0),
            "tongue": None
        }
    ],
    PuppyState.LYING_DOWN: [
        {
            "head": (0, -10, 34, 25, -10),
            "body": (0, 8, 52, 24, 0),
            "legs": [(-20, 22, 10, 14, -8), (20, 22, 10, 14, 8),
                     (-20, 22, 10, 14, -8), (20, 22, 10, 14, 8)],
            "tail": (26, 4, 18, 6, -10),
            "nose": (14, -5, 6, 5, 0),
            "eyes": [(-6, -8, 5, 3, 0), (6, -8, 5, 3, 0)],
            "tongue": None
        }
    ]
}

# 状态气泡消息
STATE_MESSAGES = {
    PuppyState.IDLE: ["汪~", "无聊...", "嘿嘿", "想玩~"],
    PuppyState.WALKING: ["溜达溜达~", "散步中", "走走走~"],
    PuppyState.SITTING: ["坐好啦~", "乖乖坐", "休息一下"],
    PuppyState.WAGGING: ["开心！", "摇尾巴~", "喜欢你！", "汪汪！"],
    PuppyState.YAWNING: ["哈~~~", "困了...", "好累啊"],
    PuppyState.STRETCHING: ["伸懒腰~", "活动一下", "嗯~舒服"],
    PuppyState.SLEEPING: ["Zzz...", "睡着了", "做梦中..."],
    PuppyState.LYING_DOWN: ["趴下~", "好懒啊", "不想动..."]
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

    def get_state_message(self) -> str:
        """获取当前状态的随机消息"""
        import random
        messages = STATE_MESSAGES.get(self.current_state, ["..."])
        return random.choice(messages)
