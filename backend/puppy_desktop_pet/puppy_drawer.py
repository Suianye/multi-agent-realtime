"""
小黑狗绘制模块
使用 Canvas 绘制小黑狗各个部件
更可爱的绘制效果
"""
import tkinter as tk
from typing import Dict, List, Optional
from animations import AnimationManager, PuppyState
from config import (COLOR_BLACK, COLOR_WHITE, COLOR_PINK, COLOR_DARK_GRAY,
                    COLOR_BROWN, COLOR_NOSE_PINK)


class PuppyDrawer:
    """小黑狗绘制器"""

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.animation_manager = AnimationManager()
        self.current_items: List[int] = []
        self.center_x = 60
        self.center_y = 70

    def draw_puppy(self, state: PuppyState = PuppyState.IDLE):
        """绘制小黑狗"""
        self.clear_puppy()
        self.animation_manager.set_state(state)
        frame = self.animation_manager.get_current_frame()
        self._draw_frame(frame)

    def _draw_frame(self, frame: Dict):
        """绘制单帧"""
        cx, cy = self.center_x, self.center_y

        # 1. 绘制尾巴（在身体后面）
        if "tail" in frame:
            tail = frame["tail"]
            tx, ty, tw, th, angle = tail
            self._draw_tail(cx + tx, cy + ty, tw, th, angle)

        # 2. 绘制身体
        body = frame["body"]
        bx, by, bw, bh, _ = body
        self._draw_body(cx + bx, cy + by, bw, bh)

        # 3. 绘制腿
        for i, leg in enumerate(frame["legs"]):
            lx, ly, lw, lh, angle = leg
            is_front = i < 2
            self._draw_leg(cx + lx, cy + ly, lw, lh, angle, is_front)

        # 4. 绘制头部
        head = frame["head"]
        hx, hy, hw, hh, angle = head
        self._draw_head(cx + hx, cy + hy, hw, hh, angle)

        # 5. 绘制眼睛
        for eye in frame["eyes"]:
            ex, ey, ew, eh, _ = eye
            self._draw_eye(cx + ex, cy + ey, ew, eh)

        # 6. 绘制鼻子
        nose = frame["nose"]
        nx, ny, nw, nh, _ = nose
        self._draw_nose(cx + nx, cy + ny, nw, nh)

        # 7. 绘制舌头（如果有的话）
        if frame.get("tongue"):
            tongue = frame["tongue"]
            tng_x, tng_y, tng_w, tng_h, _ = tongue
            self._draw_tongue(cx + tng_x, cy + tng_y, tng_w, tng_h)

        # 8. 绘制嘴巴（打哈欠时）
        if frame.get("mouth"):
            mouth = frame["mouth"]
            mx, my, mw, mh, _ = mouth
            self._draw_mouth_open(cx + mx, cy + my, mw, mh)

        # 9. 绘制 Zzz（睡觉时）
        if frame.get("zzz"):
            zzz = frame["zzz"]
            zx, zy, zw, zh, _ = zzz
            self._draw_zzz(cx + zx, cy + zy, zw, zh)

        # 10. 绘制斑点装饰
        self._draw_spots(cx, cy)

    def _draw_body(self, cx: int, cy: int, width: int, height: int):
        """绘制身体"""
        # 主体
        self.current_items.append(
            self.canvas.create_oval(
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY, width=1
            )
        )
        # 肚子（浅色区域）
        belly_h = height * 0.4
        self.current_items.append(
            self.canvas.create_oval(
                cx - width // 3, cy - belly_h // 2,
                cx + width // 3, cy + belly_h // 2,
                fill="#2a2a2a", outline=""
            )
        )

    def _draw_head(self, cx: int, cy: int, width: int, height: int, angle: float):
        """绘制头部"""
        # 主头部
        self.current_items.append(
            self.canvas.create_oval(
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY, width=1
            )
        )
        # 左耳
        ear_w = width * 0.25
        ear_h = height * 0.35
        self.current_items.append(
            self.canvas.create_polygon(
                cx - width // 2 + 2, cy - height // 4,
                cx - width // 2 - ear_w // 2, cy - height // 2 - ear_h,
                cx - width // 4, cy - height // 4,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY
            )
        )
        # 右耳
        self.current_items.append(
            self.canvas.create_polygon(
                cx + width // 2 - 2, cy - height // 4,
                cx + width // 2 + ear_w // 2, cy - height // 2 - ear_h,
                cx + width // 4, cy - height // 4,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY
            )
        )
        # 内耳（粉色）
        inner_ear_w = ear_w * 0.5
        inner_ear_h = ear_h * 0.5
        self.current_items.append(
            self.canvas.create_polygon(
                cx - width // 2 + 4, cy - height // 4 - 2,
                cx - width // 2 - inner_ear_w // 2 + 2, cy - height // 2 - inner_ear_h,
                cx - width // 4 + 2, cy - height // 4 - 2,
                fill=COLOR_PINK, outline=""
            )
        )
        self.current_items.append(
            self.canvas.create_polygon(
                cx + width // 2 - 4, cy - height // 4 - 2,
                cx + width // 2 + inner_ear_w // 2 - 2, cy - height // 2 - inner_ear_h,
                cx + width // 4 - 2, cy - height // 4 - 2,
                fill=COLOR_PINK, outline=""
            )
        )
        # 口鼻区域（浅色）
        muzzle_w = width * 0.4
        muzzle_h = height * 0.25
        self.current_items.append(
            self.canvas.create_oval(
                cx - muzzle_w // 2 + 3, cy - muzzle_h // 2 + 2,
                cx + muzzle_w // 2 + 3, cy + muzzle_h // 2 + 2,
                fill="#3a3a3a", outline=""
            )
        )

    def _draw_eye(self, cx: int, cy: int, width: int, height: int):
        """绘制眼睛"""
        # 眼白
        self.current_items.append(
            self.canvas.create_oval(
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_WHITE, outline=COLOR_DARK_GRAY, width=1
            )
        )
        # 瞳孔（如果眼睛不是闭着的）
        if height > 2:
            pupil_size = min(width, height) * 0.5
            self.current_items.append(
                self.canvas.create_oval(
                    cx - pupil_size // 2, cy - pupil_size // 2,
                    cx + pupil_size // 2, cy + pupil_size // 2,
                    fill=COLOR_BLACK, outline=""
                )
            )
            # 高光
            highlight_size = pupil_size * 0.3
            self.current_items.append(
                self.canvas.create_oval(
                    cx - pupil_size // 4 - highlight_size // 2,
                    cy - pupil_size // 4 - highlight_size // 2,
                    cx - pupil_size // 4 + highlight_size // 2,
                    cy - pupil_size // 4 + highlight_size // 2,
                    fill=COLOR_WHITE, outline=""
                )
            )

    def _draw_nose(self, cx: int, cy: int, width: int, height: int):
        """绘制鼻子"""
        self.current_items.append(
            self.canvas.create_oval(
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_NOSE_PINK, outline=COLOR_DARK_GRAY, width=1
            )
        )

    def _draw_tail(self, cx: int, cy: int, width: int, height: int, angle: float):
        """绘制尾巴"""
        # 使用弧形绘制弯曲的尾巴
        self.current_items.append(
            self.canvas.create_arc(
                cx - width, cy - height,
                cx + width, cy + height,
                start=0, extent=angle,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY, width=1
            )
        )
        # 尾巴尖（浅色）
        tip_size = 4
        tip_x = cx + width * 0.7
        tip_y = cy - height * 0.5
        self.current_items.append(
            self.canvas.create_oval(
                tip_x - tip_size, tip_y - tip_size,
                tip_x + tip_size, tip_y + tip_size,
                fill="#2a2a2a", outline=""
            )
        )

    def _draw_leg(self, cx: int, cy: int, width: int, height: int,
                  angle: float, is_front: bool):
        """绘制腿"""
        # 腿主体
        self.current_items.append(
            self.canvas.create_oval(
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY, width=1
            )
        )
        # 爪子
        paw_size = width * 0.8
        paw_y = cy + height // 2 - paw_size // 2
        self.current_items.append(
            self.canvas.create_oval(
                cx - paw_size, paw_y - paw_size // 2,
                cx + paw_size, paw_y + paw_size // 2,
                fill="#2a2a2a", outline=COLOR_DARK_GRAY, width=1
            )
        )

    def _draw_spots(self, cx: int, cy: int):
        """绘制装饰斑点"""
        # 背上的斑点
        spots = [(cx - 5, cy - 3, 4), (cx + 8, cy + 2, 3)]
        for sx, sy, size in spots:
            self.current_items.append(
                self.canvas.create_oval(
                    sx - size, sy - size,
                    sx + size, sy + size,
                    fill="#2a2a2a", outline=""
                )
            )

    def _draw_tongue(self, cx: int, cy: int, width: int, height: int):
        """绘制舌头"""
        self.current_items.append(
            self.canvas.create_oval(
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_PINK, outline=COLOR_DARK_GRAY, width=1
            )
        )

    def _draw_mouth_open(self, cx: int, cy: int, width: int, height: int):
        """绘制张开的嘴巴（打哈欠）"""
        self.current_items.append(
            self.canvas.create_oval(
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill="#4a0000", outline=COLOR_DARK_GRAY, width=1
            )
        )

    def _draw_zzz(self, cx: int, cy: int, width: int, height: int):
        """绘制睡觉的 Zzz 符号"""
        # 使用文字绘制
        self.current_items.append(
            self.canvas.create_text(
                cx, cy,
                text="Z",
                fill="#666666",
                font=("Arial", int(width * 0.8), "bold")
            )
        )
        self.current_items.append(
            self.canvas.create_text(
                cx + width * 0.6, cy - height * 0.4,
                text="z",
                fill="#888888",
                font=("Arial", int(width * 0.5), "bold")
            )
        )
        self.current_items.append(
            self.canvas.create_text(
                cx + width * 1.0, cy - height * 0.7,
                text="z",
                fill="#aaaaaa",
                font=("Arial", int(width * 0.3), "bold")
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

    def get_animation_manager(self) -> AnimationManager:
        """获取动画管理器"""
        return self.animation_manager
