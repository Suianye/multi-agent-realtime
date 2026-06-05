"""
小黑狗核心逻辑模块
管理状态机和行为
"""
import tkinter as tk
import random
from animations import PuppyState
from puppy_drawer import PuppyDrawer
from config import WALK_SPEED, IDLE_TIMEOUT, SITTING_TIMEOUT, WAGGING_TIMEOUT, CANVAS_WIDTH


class Puppy:
    """小黑狗类"""

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.drawer = PuppyDrawer(canvas)
        self.state = PuppyState.IDLE
        self.x = CANVAS_WIDTH // 2
        self.y = 60
        self.direction = 1  # 1=右，-1=左
        self.state_timer = 0
        self.update_interval = 100  # 毫秒

        # 绘制初始状态
        self.drawer.set_position(self.x, self.y)
        self.drawer.draw_puppy(self.state)

    def on_click(self):
        """点击事件处理"""
        if self.state == PuppyState.IDLE:
            self.state = PuppyState.WAGGING
            self.state_timer = 0
        elif self.state == PuppyState.WALKING:
            self.state = PuppyState.SITTING
            self.state_timer = 0
        elif self.state == PuppyState.SITTING:
            self.state = PuppyState.IDLE
            self.state_timer = 0

        self.drawer.update_animation(self.state)

    def update(self):
        """更新状态"""
        self.state_timer += self.update_interval

        if self.state == PuppyState.IDLE:
            if self.state_timer >= IDLE_TIMEOUT:
                self.state = PuppyState.WALKING
                self.state_timer = 0
                self.direction = random.choice([-1, 1])

        elif self.state == PuppyState.WALKING:
            self._move()
            self._check_boundary()

        elif self.state == PuppyState.SITTING:
            if self.state_timer >= SITTING_TIMEOUT:
                self.state = PuppyState.IDLE
                self.state_timer = 0

        elif self.state == PuppyState.WAGGING:
            if self.state_timer >= WAGGING_TIMEOUT:
                self.state = PuppyState.IDLE
                self.state_timer = 0

        # 更新动画
        self.drawer.set_position(self.x, self.y)
        self.drawer.update_animation(self.state)

    def _move(self):
        """移动小黑狗"""
        self.x += WALK_SPEED * self.direction

    def _check_boundary(self):
        """检查边界"""
        if self.x <= 10:
            self.x = 10
            self.direction = 1
        elif self.x >= CANVAS_WIDTH - 10:
            self.x = CANVAS_WIDTH - 10
            self.direction = -1

    def get_state(self) -> PuppyState:
        """获取当前状态"""
        return self.state

    def get_position(self) -> tuple:
        """获取位置"""
        return (self.x, self.y)
