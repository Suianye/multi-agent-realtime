"""
小黑狗核心逻辑模块
管理状态机和行为
包含完整的错误处理和状态验证
"""
import tkinter as tk
import random
from typing import Optional, Tuple
from animations import PuppyState
from puppy_drawer import PuppyDrawer
from config import (WALK_SPEED, IDLE_TIMEOUT, SITTING_TIMEOUT, WAGGING_TIMEOUT,
                    YAWNING_TIMEOUT, STRETCHING_TIMEOUT, SLEEPING_TIMEOUT,
                    LYING_DOWN_TIMEOUT, AUTO_ACTION_PROBABILITY,
                    CANVAS_WIDTH, CANVAS_HEIGHT, BOUNDARY_MARGIN)
from logger import get_logger, log_exception

# 模块日志记录器
logger = get_logger("puppy")

# 状态转换映射表（用于验证合法的状态转换）
VALID_STATE_TRANSITIONS = {
    PuppyState.IDLE: [PuppyState.WALKING, PuppyState.WAGGING, PuppyState.YAWNING,
                      PuppyState.STRETCHING, PuppyState.SLEEPING, PuppyState.SITTING,
                      PuppyState.LYING_DOWN],
    PuppyState.WALKING: [PuppyState.IDLE, PuppyState.SITTING, PuppyState.YAWNING,
                         PuppyState.STRETCHING, PuppyState.SLEEPING],
    PuppyState.SITTING: [PuppyState.IDLE, PuppyState.WAGGING, PuppyState.WALKING],
    PuppyState.WAGGING: [PuppyState.IDLE, PuppyState.WALKING],
    PuppyState.YAWNING: [PuppyState.IDLE, PuppyState.WALKING],
    PuppyState.STRETCHING: [PuppyState.IDLE, PuppyState.WAGGING, PuppyState.WALKING],
    PuppyState.SLEEPING: [PuppyState.YAWNING, PuppyState.IDLE],
    PuppyState.LYING_DOWN: [PuppyState.IDLE, PuppyState.WALKING],
}

# 状态超时配置映射
STATE_TIMEOUTS = {
    PuppyState.IDLE: IDLE_TIMEOUT,
    PuppyState.SITTING: SITTING_TIMEOUT,
    PuppyState.WAGGING: WAGGING_TIMEOUT,
    PuppyState.YAWNING: YAWNING_TIMEOUT,
    PuppyState.STRETCHING: STRETCHING_TIMEOUT,
    PuppyState.SLEEPING: SLEEPING_TIMEOUT,
    PuppyState.LYING_DOWN: LYING_DOWN_TIMEOUT,
}


class Puppy:
    """小黑狗类

    管理小黑狗的状态机、位置和行为。
    包含完整的错误处理和状态验证。
    """

    def __init__(self, canvas: tk.Canvas):
        """初始化小黑狗

        Args:
            canvas: tkinter Canvas 对象
        """
        if not isinstance(canvas, tk.Canvas):
            raise TypeError(f"canvas 必须是 tk.Canvas 实例，实际为 {type(canvas)}")

        self.canvas = canvas
        self.drawer = PuppyDrawer(canvas)
        self.state = PuppyState.IDLE
        self.x = CANVAS_WIDTH // 2
        self.y = 70
        self.direction = 1  # 1=右，-1=左
        self.state_timer = 0
        self.update_interval = 100  # 毫秒
        self.auto_action_counter = 0
        self._is_active = True

        # 绘制初始状态
        try:
            self.drawer.set_position(self.x, self.y)
            self.drawer.draw_puppy(self.state)
            logger.info("小黑狗已初始化")
        except Exception as e:
            log_exception(logger, "初始化小黑狗绘制失败", e)

    def _validate_state(self, state: PuppyState) -> bool:
        """验证状态是否有效

        Args:
            state: 要验证的状态

        Returns:
            状态是否有效
        """
        if not isinstance(state, PuppyState):
            logger.error(f"无效的状态类型: {type(state)}")
            return False
        return True

    def _is_valid_transition(self, new_state: PuppyState) -> bool:
        """检查状态转换是否合法

        Args:
            new_state: 新状态

        Returns:
            转换是否合法
        """
        valid_targets = VALID_STATE_TRANSITIONS.get(self.state, [])
        if new_state not in valid_targets:
            logger.warning(
                f"非法状态转换: {self.state.name} -> {new_state.name}，"
                f"允许的目标: {[s.name for s in valid_targets]}"
            )
            return False
        return True

    def on_click(self) -> None:
        """点击事件处理 - 互动动作

        根据当前状态触发不同的互动动作。
        """
        if not self._is_active:
            return

        try:
            old_state = self.state

            if self.state == PuppyState.SLEEPING:
                # 睡觉时点击会醒来
                self.state = PuppyState.YAWNING
                self.state_timer = 0
            elif self.state == PuppyState.IDLE:
                self.state = PuppyState.WAGGING
                self.state_timer = 0
            elif self.state == PuppyState.WALKING:
                self.state = PuppyState.SITTING
                self.state_timer = 0
            elif self.state == PuppyState.SITTING:
                self.state = PuppyState.WAGGING
                self.state_timer = 0
            elif self.state == PuppyState.WAGGING:
                # 连续点击会更开心
                self.state_timer = 0
            elif self.state == PuppyState.YAWNING:
                self.state = PuppyState.IDLE
                self.state_timer = 0
            elif self.state == PuppyState.STRETCHING:
                self.state = PuppyState.WAGGING
                self.state_timer = 0
            elif self.state == PuppyState.LYING_DOWN:
                # 趴下时点击会站起来
                self.state = PuppyState.IDLE
                self.state_timer = 0

            self.drawer.update_animation(self.state)

            if old_state != self.state:
                logger.debug(f"点击互动: {old_state.name} -> {self.state.name}")

        except Exception as e:
            log_exception(logger, "点击事件处理异常", e)

    def set_state(self, new_state: PuppyState) -> None:
        """设置状态

        Args:
            new_state: 新状态
        """
        if not self._validate_state(new_state):
            return

        if not self._is_active:
            logger.debug("小黑狗未激活，忽略状态设置")
            return

        try:
            if self.state != new_state:
                old_state = self.state

                # 验证状态转换（仅记录警告，不阻止）
                if not self._is_valid_transition(new_state):
                    logger.info(f"强制状态转换: {old_state.name} -> {new_state.name}")

                self.state = new_state
                self.state_timer = 0
                self.drawer.update_animation(self.state)

                logger.debug(f"状态切换: {old_state.name} -> {new_state.name}")

        except Exception as e:
            log_exception(logger, f"设置状态异常: {new_state.name}", e)

    def update(self) -> None:
        """更新状态

        每帧调用一次，更新小黑狗的状态和位置。
        """
        if not self._is_active:
            return

        try:
            self.state_timer += self.update_interval
            self.auto_action_counter += 1

            # 检查是否触发自主动作
            if self.auto_action_counter >= 10:  # 每秒检查一次
                self.auto_action_counter = 0
                self._check_auto_action()

            # 根据当前状态执行更新逻辑
            if self.state == PuppyState.IDLE:
                self._update_idle()
            elif self.state == PuppyState.WALKING:
                self._update_walking()
            elif self.state == PuppyState.SITTING:
                self._update_timed_state(PuppyState.IDLE, SITTING_TIMEOUT)
            elif self.state == PuppyState.WAGGING:
                self._update_timed_state(PuppyState.IDLE, WAGGING_TIMEOUT)
            elif self.state == PuppyState.YAWNING:
                self._update_timed_state(PuppyState.IDLE, YAWNING_TIMEOUT)
            elif self.state == PuppyState.STRETCHING:
                self._update_timed_state(PuppyState.IDLE, STRETCHING_TIMEOUT)
            elif self.state == PuppyState.SLEEPING:
                self._update_timed_state(PuppyState.YAWNING, SLEEPING_TIMEOUT)
            elif self.state == PuppyState.LYING_DOWN:
                self._update_timed_state(PuppyState.IDLE, LYING_DOWN_TIMEOUT)
            else:
                logger.warning(f"未知状态: {self.state}，重置为 IDLE")
                self.state = PuppyState.IDLE
                self.state_timer = 0

            # 更新动画
            self.drawer.set_position(self.x, self.y)
            self.drawer.update_animation(self.state)

        except Exception as e:
            log_exception(logger, "更新状态异常", e)

    def _update_idle(self) -> None:
        """更新空闲状态"""
        if self.state_timer >= IDLE_TIMEOUT:
            try:
                # 随机选择下一个动作
                action = random.choices(
                    [PuppyState.WALKING, PuppyState.YAWNING, PuppyState.STRETCHING],
                    weights=[0.5, 0.3, 0.2],
                    k=1,
                )[0]
                self.state = action
                self.state_timer = 0
                if action == PuppyState.WALKING:
                    self.direction = random.choice([-1, 1])
            except Exception as e:
                log_exception(logger, "空闲状态更新异常", e)
                self.state = PuppyState.IDLE
                self.state_timer = 0

    def _update_walking(self) -> None:
        """更新走路状态"""
        try:
            self._move()
            self._check_boundary()

            # 走一段时间后可能停下来
            if self.state_timer >= IDLE_TIMEOUT * 2:
                if random.random() < 0.3:
                    self.state = PuppyState.IDLE
                    self.state_timer = 0
        except Exception as e:
            log_exception(logger, "走路状态更新异常", e)
            self.state = PuppyState.IDLE
            self.state_timer = 0

    def _update_timed_state(self, next_state: PuppyState, timeout: int) -> None:
        """更新定时状态

        Args:
            next_state: 超时后的下一个状态
            timeout: 超时时间（毫秒）
        """
        try:
            if self.state_timer >= timeout:
                self.state = next_state
                self.state_timer = 0
        except Exception as e:
            log_exception(logger, f"定时状态更新异常: {self.state.name}", e)
            self.state = PuppyState.IDLE
            self.state_timer = 0

    def _check_auto_action(self) -> None:
        """检查是否触发自主动作"""
        if not self._is_active:
            return

        try:
            if random.random() < AUTO_ACTION_PROBABILITY:
                # 只在空闲或走路时触发自主动作
                if self.state in [PuppyState.IDLE, PuppyState.WALKING]:
                    auto_actions = [
                        PuppyState.YAWNING,
                        PuppyState.STRETCHING,
                        PuppyState.SLEEPING,
                    ]
                    action = random.choice(auto_actions)
                    old_state = self.state
                    self.state = action
                    self.state_timer = 0
                    logger.debug(f"自主动作: {old_state.name} -> {action.name}")
        except Exception as e:
            log_exception(logger, "自主动作检查异常", e)

    def _move(self) -> None:
        """移动小黑狗"""
        try:
            new_x = self.x + WALK_SPEED * self.direction

            # 确保不会溢出边界
            if new_x < 0:
                new_x = 0
            elif new_x > CANVAS_WIDTH:
                new_x = CANVAS_WIDTH

            self.x = new_x
        except Exception as e:
            log_exception(logger, "移动异常", e)

    def _check_boundary(self) -> None:
        """检查边界

        确保小黑狗不会走出 Canvas 可见区域。
        """
        try:
            margin = BOUNDARY_MARGIN

            if self.x <= margin:
                self.x = margin
                self.direction = 1
            elif self.x >= CANVAS_WIDTH - margin:
                self.x = CANVAS_WIDTH - margin
                self.direction = -1

            # 垂直边界检查（虽然通常不会改变）
            self.y = max(0, min(self.y, CANVAS_HEIGHT))

        except Exception as e:
            log_exception(logger, "边界检查异常", e)
            # 恢复到安全位置
            self.x = CANVAS_WIDTH // 2
            self.y = 70

    def get_state(self) -> PuppyState:
        """获取当前状态

        Returns:
            当前状态枚举值
        """
        return self.state

    def get_position(self) -> Tuple[int, int]:
        """获取位置

        Returns:
            (x, y) 坐标元组
        """
        return (self.x, self.y)

    def get_state_message(self) -> str:
        """获取当前状态的消息

        Returns:
            状态相关的随机消息
        """
        try:
            return self.drawer.get_animation_manager().get_state_message()
        except Exception as e:
            log_exception(logger, "获取状态消息异常", e)
            return "..."

    def set_direction(self, direction: int) -> None:
        """设置朝向

        Args:
            direction: 朝向 (1=右, -1=左)
        """
        if direction not in (1, -1):
            logger.warning(f"无效的朝向值: {direction}，使用默认值 1")
            direction = 1

        self.direction = direction

    def set_active(self, active: bool) -> None:
        """设置激活状态

        Args:
            active: 是否激活
        """
        self._is_active = active
        logger.debug(f"小黑狗{'激活' if active else '停用'}")

    def is_active(self) -> bool:
        """检查是否激活

        Returns:
            是否激活
        """
        return self._is_active

    def reset(self) -> None:
        """重置小黑狗到初始状态"""
        try:
            self.state = PuppyState.IDLE
            self.x = CANVAS_WIDTH // 2
            self.y = 70
            self.direction = 1
            self.state_timer = 0
            self.auto_action_counter = 0
            self._is_active = True

            self.drawer.set_position(self.x, self.y)
            self.drawer.draw_puppy(self.state)

            logger.info("小黑狗已重置")
        except Exception as e:
            log_exception(logger, "重置小黑狗异常", e)

    def recover(self) -> None:
        """从错误状态恢复

        当发生不可恢复的错误时调用，尝试将小黑狗恢复到安全状态。
        """
        try:
            logger.info("执行错误恢复")
            self._is_active = True
            self.state = PuppyState.IDLE
            self.state_timer = 0
            self.auto_action_counter = 0
            self.x = CANVAS_WIDTH // 2
            self.y = 70
            self.direction = 1

            try:
                self.drawer.set_position(self.x, self.y)
                self.drawer.update_animation(self.state)
            except Exception as draw_err:
                log_exception(logger, "恢复绘制失败", draw_err)

            logger.info("错误恢复完成")
        except Exception as e:
            log_exception(logger, "错误恢复失败", e)

    def get_debug_info(self) -> dict:
        """获取调试信息

        Returns:
            包含小黑狗状态的调试信息字典
        """
        return {
            "state": self.state.name,
            "position": (self.x, self.y),
            "direction": self.direction,
            "state_timer": self.state_timer,
            "auto_action_counter": self.auto_action_counter,
            "is_active": self._is_active,
            "update_interval": self.update_interval,
        }
