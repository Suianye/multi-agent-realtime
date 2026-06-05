"""
小黑狗绘制模块
使用 Canvas 绘制小黑狗各个部件
"""
import tkinter as tk
from typing import Dict, List
from animations import AnimationManager, PuppyState
from config import COLOR_BLACK, COLOR_WHITE, COLOR_PINK, COLOR_DARK_GRAY


class PuppyDrawer:
    """小黑狗绘制器"""

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.animation_manager = AnimationManager()
        self.current_items: List[int] = []
        self.center_x = 50
        self.center_y = 60

    def draw_puppy(self, state: PuppyState = PuppyState.IDLE):
        """绘制小黑狗"""
        self.clear_puppy()
        self.animation_manager.set_state(state)
        frame = self.animation_manager.get_current_frame()
        self._draw_frame(frame)

    def _draw_frame(self, frame: Dict):
        """绘制单帧"""
        cx, cy = self.center_x, self.center_y

        # 绘制身体
        body = frame["body"]
        bx, by, bw, bh, _ = body
        self.current_items.append(
            self.canvas.create_oval(
                cx + bx - bw // 2, cy + by - bh // 2,
                cx + bx + bw // 2, cy + by + bh // 2,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY
            )
        )

        # 绘制腿
        for leg in frame["legs"]:
            lx, ly, lw, lh, angle = leg
            self.current_items.append(
                self.canvas.create_oval(
                    cx + lx - lw // 2, cy + ly - lh // 2,
                    cx + lx + lw // 2, cy + ly + lh // 2,
                    fill=COLOR_BLACK, outline=COLOR_DARK_GRAY
                )
            )

        # 绘制头部
        head = frame["head"]
        hx, hy, hw, hh, _ = head
        self.current_items.append(
            self.canvas.create_oval(
                cx + hx - hw // 2, cy + hy - hh // 2,
                cx + hx + hw // 2, cy + hy + hh // 2,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY
            )
        )

        # 绘制眼睛
        for eye in frame["eyes"]:
            ex, ey, ew, eh, _ = eye
            self.current_items.append(
                self.canvas.create_oval(
                    cx + ex - ew // 2, cy + ey - eh // 2,
                    cx + ex + ew // 2, cy + ey + eh // 2,
                    fill=COLOR_WHITE, outline=COLOR_WHITE
                )
            )

        # 绘制鼻子
        nose = frame["nose"]
        nx, ny, nw, nh, _ = nose
        self.current_items.append(
            self.canvas.create_oval(
                cx + nx - nw // 2, cy + ny - nh // 2,
                cx + nx + nw // 2, cy + ny + nh // 2,
                fill=COLOR_PINK, outline=COLOR_PINK
            )
        )

        # 绘制尾巴
        tail = frame["tail"]
        tx, ty, tw, th, angle = tail
        self.current_items.append(
            self.canvas.create_arc(
                cx + tx - tw, cy + ty - th,
                cx + tx + tw, cy + ty + th,
                start=0, extent=angle,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY
            )
        )

    def update_animation(self, state: PuppyState):
        """更新动画"""
        self.animation_manager.set_state(state)
        self.animation_manager.advance_frame()
        frame = self.animation_manager.get_current_frame()
        self.clear_puppy()
        self._draw_frame(frame)

    def clear_puppy(self):
        """清除小黑狗"""
        for item in self.current_items:
            self.canvas.delete(item)
        self.current_items.clear()

    def set_position(self, x: int, y: int):
        """设置绘制位置"""
        self.center_x = x
        self.center_y = y
