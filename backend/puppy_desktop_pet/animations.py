"""
动画帧管理模块
定义小黑狗各个状态的动画帧
v3: 更多帧、更流畅的动画、眨眼动画、更丰富的气泡消息
"""
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
import random
from logger import get_logger, log_exception

# 模块日志记录器
logger = get_logger("animations")


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


# 默认帧数据（当帧数据缺失时使用）
_DEFAULT_PART = (0, 0, 10, 10, 0)
_DEFAULT_FRAME = {
    "head": _DEFAULT_PART,
    "body": _DEFAULT_PART,
    "legs": [_DEFAULT_PART] * 4,
    "tail": _DEFAULT_PART,
    "nose": _DEFAULT_PART,
    "eyes": [_DEFAULT_PART, _DEFAULT_PART],
    "tongue": None,
}

# 必需的帧部件
_REQUIRED_PARTS = {"head", "body", "legs", "tail", "nose", "eyes"}


# 动画帧定义：每个状态包含多帧，每帧定义各部件的相对位置
# 格式：{部件名: (x偏移, y偏移, 宽度, 高度, 角度)}
ANIMATION_FRAMES: Dict[PuppyState, List[Dict]] = {
    PuppyState.IDLE: [
        # 帧1: 正常站立
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -30),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 5, 0), (6, -22, 5, 5, 0)],
            "tongue": None
        },
        # 帧2: 轻微呼吸起伏
        {
            "head": (0, -26, 34, 28, 0),
            "body": (0, -1, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -9, 18, 6, -25),
            "nose": (17, -21, 6, 5, 0),
            "eyes": [(-6, -23, 5, 5, 0), (6, -23, 5, 5, 0)],
            "tongue": None
        },
        # 帧3: 眨眼
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -30),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 2, 0), (6, -22, 5, 2, 0)],  # 眯眼
            "tongue": None
        },
    ],
    PuppyState.WALKING: [
        # 帧1: 左腿前迈
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, -15), (16, 18, 9, 22, 15),
                     (-16, 18, 9, 22, 15), (16, 18, 9, 22, -15)],
            "tail": (22, -8, 18, 6, -20),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 5, 0), (6, -22, 5, 5, 0)],
            "tongue": None
        },
        # 帧2: 过渡（身体微抬）
        {
            "head": (0, -27, 34, 28, 0),
            "body": (0, -2, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 8), (16, 18, 9, 22, -8),
                     (-16, 18, 9, 22, -8), (16, 18, 9, 22, 8)],
            "tail": (22, -10, 18, 6, -40),
            "nose": (17, -22, 6, 5, 0),
            "eyes": [(-6, -24, 5, 5, 0), (6, -24, 5, 5, 0)],
            "tongue": (12, -14, 5, 8, 0)
        },
        # 帧3: 右腿前迈
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 12), (16, 18, 9, 22, -12),
                     (-16, 18, 9, 22, -12), (16, 18, 9, 22, 12)],
            "tail": (22, -8, 18, 6, -35),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 5, 0), (6, -22, 5, 5, 0)],
            "tongue": None
        },
        # 帧4: 过渡（身体微落）
        {
            "head": (0, -24, 34, 28, 0),
            "body": (0, 1, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, -5), (16, 18, 9, 22, 5),
                     (-16, 18, 9, 22, 5), (16, 18, 9, 22, -5)],
            "tail": (22, -7, 18, 6, -25),
            "nose": (17, -19, 6, 5, 0),
            "eyes": [(-6, -21, 5, 5, 0), (6, -21, 5, 5, 0)],
            "tongue": None
        },
    ],
    PuppyState.SITTING: [
        # 帧1: 坐好
        {
            "head": (0, -18, 34, 28, 0),
            "body": (0, 5, 44, 28, 0),
            "legs": [(-16, 22, 9, 16, 0), (16, 22, 9, 16, 0),
                     (-16, 22, 9, 16, 35), (16, 22, 9, 16, -35)],
            "tail": (22, -2, 18, 6, -10),
            "nose": (17, -13, 6, 5, 0),
            "eyes": [(-6, -16, 5, 5, 0), (6, -16, 5, 5, 0)],
            "tongue": None
        },
        # 帧2: 轻微摇晃
        {
            "head": (1, -18, 34, 28, 2),
            "body": (0, 5, 44, 28, 0),
            "legs": [(-16, 22, 9, 16, 0), (16, 22, 9, 16, 0),
                     (-16, 22, 9, 16, 35), (16, 22, 9, 16, -35)],
            "tail": (22, -2, 18, 6, -15),
            "nose": (18, -13, 6, 5, 0),
            "eyes": [(-5, -16, 5, 5, 0), (7, -16, 5, 5, 0)],
            "tongue": None
        },
    ],
    PuppyState.WAGGING: [
        # 帧1: 尾巴高翘（开心）
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -55),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 6, 0), (6, -22, 5, 6, 0)],
            "tongue": (12, -15, 5, 10, 0)
        },
        # 帧2: 尾巴左摆
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -10),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 6, 0), (6, -22, 5, 6, 0)],
            "tongue": (12, -15, 5, 10, 0)
        },
        # 帧3: 尾巴右摆
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -60),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 6, 0), (6, -22, 5, 6, 0)],
            "tongue": (12, -15, 5, 10, 0)
        },
    ],
    PuppyState.YAWNING: [
        # 帧1: 张嘴打哈欠
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
        # 帧2: 嘴巴稍小
        {
            "head": (0, -24, 34, 29, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -20),
            "nose": (17, -19, 6, 5, 0),
            "eyes": [(-6, -22, 5, 2, 0), (6, -22, 5, 2, 0)],
            "mouth": (12, -14, 8, 8, 0),
            "tongue": None
        },
        # 帧3: 闭嘴
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -20),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 2, 0), (6, -22, 5, 2, 0)],
            "mouth": None,
            "tongue": None
        },
    ],
    PuppyState.STRETCHING: [
        # 帧1: 前伸
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
        # 帧2: 舒展
        {
            "head": (8, -22, 34, 28, 5),
            "body": (2, 0, 48, 30, 2),
            "legs": [(-18, 17, 9, 24, -8), (18, 17, 9, 24, 8),
                     (-18, 17, 9, 24, -5), (18, 17, 9, 24, 5)],
            "tail": (25, -6, 19, 6, -35),
            "nose": (25, -17, 6, 5, 0),
            "eyes": [(-1, -20, 5, 4, 0), (7, -20, 5, 4, 0)],
            "tongue": (12, -15, 5, 8, 0)
        },
        # 帧3: 恢复
        {
            "head": (0, -25, 34, 28, 0),
            "body": (0, 0, 44, 34, 0),
            "legs": [(-16, 18, 9, 22, 0), (16, 18, 9, 22, 0),
                     (-16, 18, 9, 22, 0), (16, 18, 9, 22, 0)],
            "tail": (22, -8, 18, 6, -40),
            "nose": (17, -20, 6, 5, 0),
            "eyes": [(-6, -22, 5, 4, 0), (6, -22, 5, 4, 0)],
            "tongue": (12, -15, 5, 8, 0)
        },
    ],
    PuppyState.SLEEPING: [
        # 帧1: 睡姿1 + Zzz
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
        # 帧2: 睡姿2 + Zzz 偏移
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
        },
        # 帧3: 呼吸起伏
        {
            "head": (0, -14, 34, 25, -15),
            "body": (0, 6, 48, 28, 0),
            "legs": [(-18, 20, 10, 18, -5), (18, 20, 10, 18, 5),
                     (-18, 20, 10, 18, -5), (18, 20, 10, 18, 5)],
            "tail": (24, 3, 18, 6, -15),
            "nose": (12, -9, 6, 5, 0),
            "eyes": [(-8, -12, 6, 1, 0), (2, -12, 6, 1, 0)],
            "zzz": (22, -32, 14, 14, 0),
            "tongue": None
        },
    ],
    PuppyState.LYING_DOWN: [
        # 帧1: 趴下
        {
            "head": (0, -10, 34, 25, -10),
            "body": (0, 8, 52, 24, 0),
            "legs": [(-20, 22, 10, 14, -8), (20, 22, 10, 14, 8),
                     (-20, 22, 10, 14, -8), (20, 22, 10, 14, 8)],
            "tail": (26, 4, 18, 6, -10),
            "nose": (14, -5, 6, 5, 0),
            "eyes": [(-6, -8, 5, 3, 0), (6, -8, 5, 3, 0)],
            "tongue": None
        },
        # 帧2: 头微抬
        {
            "head": (0, -12, 34, 25, -8),
            "body": (0, 8, 52, 24, 0),
            "legs": [(-20, 22, 10, 14, -8), (20, 22, 10, 14, 8),
                     (-20, 22, 10, 14, -8), (20, 22, 10, 14, 8)],
            "tail": (26, 4, 18, 6, -15),
            "nose": (14, -7, 6, 5, 0),
            "eyes": [(-6, -10, 5, 4, 0), (6, -10, 5, 4, 0)],
            "tongue": None
        },
    ]
}

# 状态气泡消息
STATE_MESSAGES: Dict[PuppyState, List[str]] = {
    PuppyState.IDLE: ["汪~", "无聊...", "嘿嘿", "想玩~", "你好呀！", "在干嘛？", "摸摸我~"],
    PuppyState.WALKING: ["溜达溜达~", "散步中", "走走走~", "探险去！", "跑跑跑~", "这边走~"],
    PuppyState.SITTING: ["坐好啦~", "乖乖坐", "休息一下", "等你哦~", "乖巧.jpg"],
    PuppyState.WAGGING: ["开心！", "摇尾巴~", "喜欢你！", "汪汪！", "好开心呀！", "最喜欢你了~", "爱你哦~"],
    PuppyState.YAWNING: ["哈~~~", "困了...", "好累啊", "打哈欠~", "好困好困", "需要充电..."],
    PuppyState.STRETCHING: ["伸懒腰~", "活动一下", "嗯~舒服", "动一动~", "元气满满！"],
    PuppyState.SLEEPING: ["Zzz...", "睡着了", "做梦中...", "呼呼~", "别吵醒我...", "梦见骨头了~"],
    PuppyState.LYING_DOWN: ["趴下~", "好懒啊", "不想动...", "躺着好舒服", "趴趴~", "休息中..."],
}


def validate_frame_part(part: Any, part_name: str) -> bool:
    """验证帧部件数据格式

    Args:
        part: 部件数据
        part_name: 部件名称（用于日志）

    Returns:
        数据是否有效
    """
    if part is None:
        return True  # None 表示可选部件不存在

    if isinstance(part, list):
        # 列表形式（如 legs, eyes）
        if len(part) == 0:
            logger.warning(f"帧部件 '{part_name}' 列表为空")
            return False
        for i, item in enumerate(part):
            if not isinstance(item, (tuple, list)) or len(item) != 5:
                logger.warning(f"帧部件 '{part_name}[{i}]' 格式错误: 需要5元组")
                return False
        return True

    if isinstance(part, (tuple, list)):
        if len(part) != 5:
            logger.warning(f"帧部件 '{part_name}' 格式错误: 需要5元组，实际长度 {len(part)}")
            return False
        return True

    logger.warning(f"帧部件 '{part_name}' 类型错误: {type(part)}")
    return False


def validate_frame(frame: Dict, state_name: str, frame_index: int) -> bool:
    """验证单帧数据完整性

    Args:
        frame: 帧数据字典
        state_name: 状态名称（用于日志）
        frame_index: 帧索引（用于日志）

    Returns:
        帧数据是否有效
    """
    if not isinstance(frame, dict):
        logger.error(f"帧数据类型错误: {state_name}[{frame_index}] 期望 dict，实际 {type(frame)}")
        return False

    # 检查必需部件
    for part_name in _REQUIRED_PARTS:
        if part_name not in frame:
            logger.warning(f"帧数据缺少必需部件: {state_name}[{frame_index}].{part_name}")
            return False
        if not validate_frame_part(frame[part_name], part_name):
            return False

    # 验证可选部件
    for part_name in ["tongue", "mouth", "zzz"]:
        if part_name in frame:
            if not validate_frame_part(frame[part_name], part_name):
                return False

    return True


def get_safe_frame(state: PuppyState, frame_index: int) -> Dict:
    """安全地获取帧数据，包含错误恢复

    Args:
        state: 小黑狗状态
        frame_index: 帧索引

    Returns:
        帧数据字典，如果出错则返回默认帧
    """
    try:
        if state not in ANIMATION_FRAMES:
            logger.error(f"未知状态: {state}，使用默认帧")
            return _DEFAULT_FRAME.copy()

        frames = ANIMATION_FRAMES[state]
        if not frames:
            logger.error(f"状态 '{state.name}' 没有定义帧数据，使用默认帧")
            return _DEFAULT_FRAME.copy()

        # 安全的索引取模
        safe_index = frame_index % len(frames)
        frame = frames[safe_index]

        if not validate_frame(frame, state.name, safe_index):
            logger.warning(f"帧数据验证失败: {state.name}[{safe_index}]，使用默认帧")
            return _DEFAULT_FRAME.copy()

        return frame

    except Exception as e:
        log_exception(logger, f"获取帧数据异常: {state.name}[{frame_index}]", e)
        return _DEFAULT_FRAME.copy()


class AnimationManager:
    """动画管理器

    管理动画状态和帧切换，包含完整的错误处理。
    """

    def __init__(self):
        self._current_state = PuppyState.IDLE
        self._current_frame = 0
        self._frames = ANIMATION_FRAMES
        self._state_valid = True
        self._blink_counter = 0
        self._blink_interval = 30  # 每30帧眨一次眼
        self._is_blinking = False

        # 初始化时验证数据完整性
        self._validate_animation_data()

        logger.debug("动画管理器已初始化")

    def _validate_animation_data(self) -> None:
        """验证动画数据完整性"""
        missing_states = []
        for state in PuppyState:
            if state not in self._frames:
                missing_states.append(state.name)
            elif not self._frames[state]:
                logger.warning(f"状态 '{state.name}' 帧列表为空")

        if missing_states:
            logger.warning(f"以下状态缺少帧定义: {', '.join(missing_states)}")
            self._state_valid = False

    def get_current_frame(self) -> Dict:
        """获取当前帧数据

        自动处理眨眼动画：在正常帧基础上叠加眨眼效果。

        Returns:
            帧数据字典，包含所有部件的位置信息
        """
        frame = get_safe_frame(self._current_state, self._current_frame)

        # 眨眼逻辑（仅在站立和走路状态生效）
        if self._current_state in [PuppyState.IDLE, PuppyState.WALKING]:
            self._blink_counter += 1
            if self._blink_counter >= self._blink_interval:
                self._is_blinking = True
                self._blink_counter = 0
                # 返回眨眼帧（眼睛高度缩小）
                blink_frame = frame.copy()
                blink_eyes = []
                for eye in frame["eyes"]:
                    ex, ey, ew, eh, ea = eye
                    blink_eyes.append((ex, ey, ew, 2, ea))  # 眯眼
                blink_frame["eyes"] = blink_eyes
                return blink_frame
            else:
                self._is_blinking = False

        return frame

    def is_blinking(self) -> bool:
        """是否正在眨眼"""
        return self._is_blinking

    def advance_frame(self) -> None:
        """推进到下一帧"""
        try:
            state_frames = self._frames.get(self._current_state, [])
            if not state_frames:
                logger.warning(f"状态 '{self._current_state.name}' 无帧数据，重置到第0帧")
                self._current_frame = 0
                return

            self._current_frame = (self._current_frame + 1) % len(state_frames)

        except Exception as e:
            log_exception(logger, "推进帧异常", e)
            self._current_frame = 0

    def set_state(self, state: PuppyState) -> None:
        """设置状态

        Args:
            state: 新状态

        Raises:
            ValueError: 如果状态无效（在非严格模式下仅记录警告）
        """
        if not isinstance(state, PuppyState):
            logger.error(f"无效的状态类型: {type(state)}，期望 PuppyState")
            return

        if self._current_state != state:
            old_state = self._current_state
            self._current_state = state
            self._current_frame = 0
            logger.debug(f"状态切换: {old_state.name} -> {state.name}")

    def get_state(self) -> PuppyState:
        """获取当前状态"""
        return self._current_state

    def get_state_message(self) -> str:
        """获取当前状态的随机消息

        Returns:
            随机选择的状态消息
        """
        import random

        try:
            messages = STATE_MESSAGES.get(self._current_state)
            if not messages:
                logger.warning(f"状态 '{self._current_state.name}' 没有消息定义")
                return "..."

            return random.choice(messages)

        except Exception as e:
            log_exception(logger, "获取状态消息异常", e)
            return "..."

    def get_frame_count(self) -> int:
        """获取当前状态的帧数

        Returns:
            帧数，如果出错返回 1
        """
        try:
            frames = self._frames.get(self._current_state, [])
            return max(1, len(frames))
        except Exception:
            return 1

    def reset(self) -> None:
        """重置动画状态"""
        self._current_state = PuppyState.IDLE
        self._current_frame = 0
        logger.debug("动画状态已重置")
