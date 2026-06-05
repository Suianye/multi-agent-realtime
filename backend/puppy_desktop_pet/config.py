"""
小黑狗桌宠配置模块
集中管理所有配置常量，包含输入验证
"""
from typing import Any, Dict, Tuple

# ============================================================
# 配置常量
# ============================================================

# 小黑狗尺寸（像素）
PUPPY_SIZE = 80

# 移动速度（像素/帧）
WALK_SPEED = 2

# 动画帧率
ANIMATION_FPS = 8

# 空闲超时（毫秒）
IDLE_TIMEOUT = 3000

# 坐下超时（毫秒）
SITTING_TIMEOUT = 3000

# 摇尾巴超时（毫秒）
WAGGING_TIMEOUT = 2000

# 打哈欠超时（毫秒）
YAWNING_TIMEOUT = 2500

# 伸懒腰超时（毫秒）
STRETCHING_TIMEOUT = 2000

# 睡觉超时（毫秒）
SLEEPING_TIMEOUT = 5000

# 趴下超时（毫秒）
LYING_DOWN_TIMEOUT = 4000

# 自主动作触发概率（每秒）
AUTO_ACTION_PROBABILITY = 0.02

# 颜色配置
COLOR_BLACK = "#1a1a1a"  # 更柔和的黑色
COLOR_WHITE = "#FFFFFF"
COLOR_PINK = "#FFB6C1"
COLOR_DARK_GRAY = "#2d2d2d"
COLOR_BROWN = "#8B4513"
COLOR_LIGHT_GRAY = "#f5f5f5"
COLOR_NOSE_PINK = "#FF69B4"

# 窗口配置
WINDOW_TITLE = "小黑狗桌宠"
CANVAS_WIDTH = 120
CANVAS_HEIGHT = 140

# 气泡配置（v3 增强样式）
BUBBLE_FONT = ("微软雅黑", 9, "bold")
BUBBLE_BG = "#fff8f0"  # 暖色调背景
BUBBLE_FG = "#5a3e28"  # 棕色文字
BUBBLE_BORDER_COLOR = "#e8c9a0"  # 边框颜色
BUBBLE_SHADOW_COLOR = "#cccccc"  # 阴影颜色
BUBBLE_DURATION = 2500  # 气泡显示时长（毫秒）

# 拖拽配置
DRAG_THRESHOLD = 5  # 拖拽阈值（像素）
DOUBLE_CLICK_DELAY = 300  # 双击延迟（毫秒）

# 边界安全边距
BOUNDARY_MARGIN = 15

# ============================================================
# 配置验证
# ============================================================

# 配置参数的合法范围定义
CONFIG_RANGES: Dict[str, Dict[str, Any]] = {
    "PUPPY_SIZE": {"min": 20, "max": 200, "type": int},
    "WALK_SPEED": {"min": 1, "max": 10, "type": (int, float)},
    "ANIMATION_FPS": {"min": 1, "max": 60, "type": int},
    "IDLE_TIMEOUT": {"min": 500, "max": 30000, "type": int},
    "SITTING_TIMEOUT": {"min": 500, "max": 30000, "type": int},
    "WAGGING_TIMEOUT": {"min": 500, "max": 30000, "type": int},
    "YAWNING_TIMEOUT": {"min": 500, "max": 30000, "type": int},
    "STRETCHING_TIMEOUT": {"min": 500, "max": 30000, "type": int},
    "SLEEPING_TIMEOUT": {"min": 500, "max": 60000, "type": int},
    "LYING_DOWN_TIMEOUT": {"min": 500, "max": 30000, "type": int},
    "AUTO_ACTION_PROBABILITY": {"min": 0.0, "max": 1.0, "type": (int, float)},
    "CANVAS_WIDTH": {"min": 50, "max": 500, "type": int},
    "CANVAS_HEIGHT": {"min": 50, "max": 500, "type": int},
    "BUBBLE_DURATION": {"min": 500, "max": 10000, "type": int},
    "DRAG_THRESHOLD": {"min": 1, "max": 50, "type": int},
    "DOUBLE_CLICK_DELAY": {"min": 100, "max": 1000, "type": int},
    "BOUNDARY_MARGIN": {"min": 0, "max": 50, "type": int},
}


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


def validate_config_value(name: str, value: Any, strict: bool = False) -> Any:
    """验证单个配置值

    Args:
        name: 配置参数名称
        value: 配置值
        strict: 严格模式下抛出异常，非严格模式下返回修正后的值

    Returns:
        验证后的值（可能被修正）

    Raises:
        ConfigValidationError: 严格模式下验证失败时抛出
    """
    if name not in CONFIG_RANGES:
        return value  # 未定义范围的参数不做验证

    spec = CONFIG_RANGES[name]
    expected_type = spec["type"]
    min_val = spec["min"]
    max_val = spec["max"]

    # 类型检查
    if not isinstance(value, expected_type):
        msg = f"配置参数 '{name}' 类型错误: 期望 {expected_type}，实际 {type(value)}"
        if strict:
            raise ConfigValidationError(msg)
        # 尝试类型转换
        try:
            if expected_type == int:
                value = int(value)
            elif isinstance(expected_type, tuple):
                for t in expected_type:
                    try:
                        value = t(value)
                        break
                    except (ValueError, TypeError):
                        continue
        except (ValueError, TypeError):
            raise ConfigValidationError(f"{msg}，且无法转换")

    # 范围检查
    if value < min_val:
        msg = f"配置参数 '{name}' 值 {value} 小于最小值 {min_val}"
        if strict:
            raise ConfigValidationError(msg)
        return min_val

    if value > max_val:
        msg = f"配置参数 '{name}' 值 {value} 大于最大值 {max_val}"
        if strict:
            raise ConfigValidationError(msg)
        return max_val

    return value


def validate_all_configs(strict: bool = False) -> Dict[str, str]:
    """验证所有配置参数

    Args:
        strict: 严格模式下遇到第一个错误就抛出异常

    Returns:
        验证错误列表（键为参数名，值为错误信息），空字典表示全部通过
    """
    errors = {}
    module_globals = globals()

    for name in CONFIG_RANGES:
        if name in module_globals:
            value = module_globals[name]
            try:
                validate_config_value(name, value, strict=strict)
            except ConfigValidationError as e:
                errors[name] = str(e)

    return errors


def validate_color(color: str) -> bool:
    """验证颜色值格式

    Args:
        color: 颜色字符串（如 "#FF0000"）

    Returns:
        是否为有效的颜色值
    """
    if not isinstance(color, str):
        return False

    # 支持 #RGB 和 #RRGGBB 格式
    if not color.startswith("#"):
        return False

    hex_part = color[1:]
    if len(hex_part) not in (3, 6):
        return False

    try:
        int(hex_part, 16)
        return True
    except ValueError:
        return False


def validate_position(x: int, y: int, screen_width: int = None,
                      screen_height: int = None) -> Tuple[int, int]:
    """验证并修正窗口位置

    Args:
        x: x 坐标
        y: y 坐标
        screen_width: 屏幕宽度（可选）
        screen_height: 屏幕高度（可选）

    Returns:
        修正后的 (x, y) 坐标
    """
    # 基本类型检查
    x = int(x) if x is not None else 0
    y = int(y) if y is not None else 0

    # 确保不为负数
    x = max(0, x)
    y = max(0, y)

    # 如果提供了屏幕尺寸，确保不超出屏幕
    if screen_width is not None:
        x = min(x, screen_width - CANVAS_WIDTH)
    if screen_height is not None:
        y = min(y, screen_height - CANVAS_HEIGHT)

    return (x, y)


def get_config_summary() -> Dict[str, Any]:
    """获取当前配置摘要（用于调试）

    Returns:
        配置参数字典
    """
    summary = {}
    for name in CONFIG_RANGES:
        value = globals().get(name)
        if value is not None:
            summary[name] = value
    return summary
