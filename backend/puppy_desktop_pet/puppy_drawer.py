"""
小黑狗绘制模块 v3
使用 Canvas 绘制小黑狗各个部件
增强：腮红、眼睛高光动画、更精致的耳朵和爪子

增强功能:
    1. Canvas 状态安全检查
    2. 坐标边界验证
    3. 绘制异常隔离
    4. 资源清理保护
    5. 性能优化（减少不必要的重绘）
"""
import tkinter as tk
from typing import Dict, List, Optional, Tuple
from animations import AnimationManager, PuppyState
from config import (COLOR_BLACK, COLOR_WHITE, COLOR_PINK, COLOR_DARK_GRAY,
                    COLOR_BROWN, COLOR_NOSE_PINK, CANVAS_WIDTH, CANVAS_HEIGHT,
                    clamp_value)
from logger import get_logger, log_exception

# 模块日志记录器
logger = get_logger("puppy_drawer")


class PuppyDrawer:
    """小黑狗绘制器

    负责在 Canvas 上绘制小黑狗的各个部件。
    包含完整的错误处理，确保绘制异常不会导致程序崩溃。
    """

    def __init__(self, canvas: tk.Canvas):
        """初始化绘制器

        Args:
            canvas: tkinter Canvas 对象
        """
        if not isinstance(canvas, tk.Canvas):
            raise TypeError(f"canvas 必须是 tk.Canvas 实例，实际为 {type(canvas)}")

        self.canvas = canvas
        self.animation_manager = AnimationManager()
        self.current_items: List[int] = []
        self.center_x = CANVAS_WIDTH // 2
        self.center_y = 70
        self._canvas_valid = True
        self._highlight_phase = 0  # 高光动画相位

        logger.debug("绘制器已初始化")

    def _check_canvas(self) -> bool:
        """检查 Canvas 是否可用

        Returns:
            Canvas 是否可用
        """
        if not self._canvas_valid:
            return False

        try:
            # 尝试访问 Canvas 属性来验证其有效性
            self.canvas.winfo_exists()
            return True
        except (tk.TclError, AttributeError):
            self._canvas_valid = False
            logger.warning("Canvas 不可用")
            return False

    def draw_puppy(self, state: PuppyState = PuppyState.IDLE) -> None:
        """绘制小黑狗

        Args:
            state: 初始状态
        """
        if not self._check_canvas():
            return

        if not isinstance(state, PuppyState):
            logger.warning(f"无效的状态类型: {type(state)}，使用 IDLE")
            state = PuppyState.IDLE

        try:
            self.clear_puppy()
            self.animation_manager.set_state(state)
            frame = self.animation_manager.get_current_frame()
            self._draw_frame(frame)
            logger.debug(f"绘制小黑狗: {state.name}")
        except Exception as e:
            log_exception(logger, f"绘制小黑狗异常: {state.name}", e)

    def _safe_create_item(self, create_func, *args, **kwargs) -> Optional[int]:
        """安全创建 Canvas 项目

        Args:
            create_func: Canvas 创建函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            项目 ID，失败返回 None
        """
        if not self._check_canvas():
            return None

        try:
            item_id = create_func(*args, **kwargs)
            if item_id is not None:
                self.current_items.append(item_id)
            return item_id
        except tk.TclError as e:
            logger.debug(f"Canvas 创建项目 Tcl 错误: {e}")
            return None
        except Exception as e:
            log_exception(logger, "Canvas 创建项目异常", e)
            return None

    def _validate_part_coords(self, cx: int, cy: int, width: int, height: int,
                               part_name: str = "") -> bool:
        """验证部件坐标是否在合理范围内

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
            width: 宽度
            height: 高度
            part_name: 部件名称（用于日志）

        Returns:
            坐标是否合理
        """
        # 基本有效性检查
        try:
            cx = int(cx)
            cy = int(cy)
            width = int(width)
            height = int(height)
        except (ValueError, TypeError):
            logger.debug(f"部件 '{part_name}' 坐标类型错误")
            return False

        if width <= 0 or height <= 0:
            logger.debug(f"部件 '{part_name}' 尺寸无效: {width}x{height}")
            return False

        # 检查是否在可见区域附近（允许一定超出）
        margin = 150
        if (cx < -margin or cx > CANVAS_WIDTH + margin or
            cy < -margin or cy > CANVAS_HEIGHT + margin):
            logger.debug(f"部件 '{part_name}' 超出可见区域: ({cx}, {cy})")
            return False

        # 检查坐标是否为 NaN 或无穷大
        if cx != cx or cy != cy:
            logger.debug(f"部件 '{part_name}' 坐标为 NaN")
            return False

        return True

    def _safe_coords(self, cx: int, cy: int, width: int, height: int) -> Tuple[int, int, int, int]:
        """安全的坐标转换（自动限制在合理范围）

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
            width: 宽度
            height: 高度

        Returns:
            修正后的 (cx, cy, width, height)
        """
        try:
            cx = int(clamp_value(cx, -200, CANVAS_WIDTH + 200))
            cy = int(clamp_value(cy, -200, CANVAS_HEIGHT + 200))
            width = int(clamp_value(width, 1, 500))
            height = int(clamp_value(height, 1, 500))
        except Exception:
            cx, cy = CANVAS_WIDTH // 2, 70
            width, height = 44, 34

        return cx, cy, width, height

    def _draw_frame(self, frame: Dict) -> None:
        """绘制单帧

        Args:
            frame: 帧数据字典
        """
        if not isinstance(frame, dict):
            logger.error(f"帧数据类型错误: {type(frame)}")
            return

        cx, cy = self.center_x, self.center_y

        # 更新高光动画相位
        self._highlight_phase = (self._highlight_phase + 1) % 60

        try:
            # 1. 绘制尾巴（在身体后面）
            if "tail" in frame and frame["tail"] is not None:
                tail = frame["tail"]
                if isinstance(tail, (tuple, list)) and len(tail) >= 5:
                    tx, ty, tw, th, angle = tail[:5]
                    self._draw_tail(cx + tx, cy + ty, tw, th, angle)

            # 2. 绘制身体
            body = frame.get("body")
            if isinstance(body, (tuple, list)) and len(body) >= 5:
                bx, by, bw, bh, _ = body[:5]
                self._draw_body(cx + bx, cy + by, bw, bh)

            # 3. 绘制腿
            legs = frame.get("legs", [])
            if isinstance(legs, (tuple, list)):
                for i, leg in enumerate(legs):
                    if isinstance(leg, (tuple, list)) and len(leg) >= 5:
                        lx, ly, lw, lh, angle = leg[:5]
                        is_front = i < 2
                        self._draw_leg(cx + lx, cy + ly, lw, lh, angle, is_front)

            # 4. 绘制头部
            head = frame.get("head")
            if isinstance(head, (tuple, list)) and len(head) >= 5:
                hx, hy, hw, hh, angle = head[:5]
                self._draw_head(cx + hx, cy + hy, hw, hh, angle)

            # 5. 绘制眼睛
            eyes = frame.get("eyes", [])
            if isinstance(eyes, (tuple, list)):
                for eye in eyes:
                    if isinstance(eye, (tuple, list)) and len(eye) >= 5:
                        ex, ey, ew, eh, _ = eye[:5]
                        self._draw_eye(cx + ex, cy + ey, ew, eh)

            # 6. 绘制鼻子
            nose = frame.get("nose")
            if isinstance(nose, (tuple, list)) and len(nose) >= 5:
                nx, ny, nw, nh, _ = nose[:5]
                self._draw_nose(cx + nx, cy + ny, nw, nh)

            # 7. 绘制舌头（如果有的话）
            tongue = frame.get("tongue")
            if tongue is not None and isinstance(tongue, (tuple, list)) and len(tongue) >= 5:
                tng_x, tng_y, tng_w, tng_h, _ = tongue[:5]
                self._draw_tongue(cx + tng_x, cy + tng_y, tng_w, tng_h)

            # 8. 绘制嘴巴（打哈欠时）
            mouth = frame.get("mouth")
            if mouth is not None and isinstance(mouth, (tuple, list)) and len(mouth) >= 5:
                mx, my, mw, mh, _ = mouth[:5]
                self._draw_mouth_open(cx + mx, cy + my, mw, mh)

            # 9. 绘制 Zzz（睡觉时）
            zzz = frame.get("zzz")
            if zzz is not None and isinstance(zzz, (tuple, list)) and len(zzz) >= 5:
                zx, zy, zw, zh, _ = zzz[:5]
                self._draw_zzz(cx + zx, cy + zy, zw, zh)

            # 10. 绘制腮红（可爱装饰）
            head_data = frame.get("head")
            if isinstance(head_data, (tuple, list)) and len(head_data) >= 4:
                self._draw_blush(cx + head_data[0], cy + head_data[1], head_data[2], head_data[3])

            # 11. 绘制斑点装饰
            self._draw_spots(cx, cy)

        except Exception as e:
            log_exception(logger, "绘制帧异常", e)

    def _draw_body(self, cx: int, cy: int, width: int, height: int) -> None:
        """绘制身体

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
            width: 宽度
            height: 高度
        """
        # 安全坐标转换
        cx, cy, width, height = self._safe_coords(cx, cy, width, height)

        if not self._validate_part_coords(cx, cy, width, height, "body"):
            return

        try:
            # 主体
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY, width=1,
            )
            # 肚子（浅色区域）
            belly_h = int(height * 0.4)
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 3, cy - belly_h // 2,
                cx + width // 3, cy + belly_h // 2,
                fill="#2a2a2a", outline="",
            )
            # 身体高光
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 4, cy - height // 3,
                cx - width // 4 + 5, cy - height // 3 + 4,
                fill="#3a3a3a", outline="",
            )
        except Exception as e:
            log_exception(logger, "绘制身体异常", e)

    def _draw_head(self, cx: int, cy: int, width: int, height: int, angle: float) -> None:
        """绘制头部

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
            width: 宽度
            height: 高度
            angle: 角度
        """
        # 安全坐标转换
        cx, cy, width, height = self._safe_coords(cx, cy, width, height)

        if not self._validate_part_coords(cx, cy, width, height, "head"):
            return

        try:
            # 主头部
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY, width=1,
            )

            # 左耳
            ear_w = width * 0.25
            ear_h = height * 0.35
            self._safe_create_item(
                self.canvas.create_polygon,
                cx - width // 2 + 2, cy - height // 4,
                cx - width // 2 - ear_w // 2, cy - height // 2 - ear_h,
                cx - width // 4, cy - height // 4,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY,
            )

            # 右耳
            self._safe_create_item(
                self.canvas.create_polygon,
                cx + width // 2 - 2, cy - height // 4,
                cx + width // 2 + ear_w // 2, cy - height // 2 - ear_h,
                cx + width // 4, cy - height // 4,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY,
            )

            # 内耳（粉色）
            inner_ear_w = ear_w * 0.5
            inner_ear_h = ear_h * 0.5
            self._safe_create_item(
                self.canvas.create_polygon,
                cx - width // 2 + 4, cy - height // 4 - 2,
                cx - width // 2 - inner_ear_w // 2 + 2, cy - height // 2 - inner_ear_h,
                cx - width // 4 + 2, cy - height // 4 - 2,
                fill=COLOR_PINK, outline="",
            )
            self._safe_create_item(
                self.canvas.create_polygon,
                cx + width // 2 - 4, cy - height // 4 - 2,
                cx + width // 2 + inner_ear_w // 2 - 2, cy - height // 2 - inner_ear_h,
                cx + width // 4 - 2, cy - height // 4 - 2,
                fill=COLOR_PINK, outline="",
            )

            # 口鼻区域（浅色）
            muzzle_w = width * 0.42
            muzzle_h = height * 0.28
            self._safe_create_item(
                self.canvas.create_oval,
                cx - muzzle_w // 2 + 3, cy - muzzle_h // 2 + 2,
                cx + muzzle_w // 2 + 3, cy + muzzle_h // 2 + 2,
                fill="#3a3a3a", outline="",
            )

            # 头部高光
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 3, cy - height // 2 + 3,
                cx - width // 3 + 5, cy - height // 2 + 7,
                fill="#333333", outline="",
            )

        except Exception as e:
            log_exception(logger, "绘制头部异常", e)

    def _draw_eye(self, cx: int, cy: int, width: int, height: int) -> None:
        """绘制眼睛

        包含眼白、瞳孔和双高光（高光有微动画）。

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
            width: 宽度
            height: 高度
        """
        if not self._validate_part_coords(cx, cy, width, height, "eye"):
            return

        try:
            # 眼白
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_WHITE, outline=COLOR_DARK_GRAY, width=1,
            )

            # 瞳孔（如果眼睛不是闭着的）
            if height > 2:
                pupil_size = min(width, height) * 0.55
                self._safe_create_item(
                    self.canvas.create_oval,
                    cx - pupil_size // 2, cy - pupil_size // 2,
                    cx + pupil_size // 2, cy + pupil_size // 2,
                    fill=COLOR_BLACK, outline="",
                )

                # 主高光（带微动画偏移）
                highlight_size = pupil_size * 0.35
                offset = 0.5 if (self._highlight_phase % 20 < 10) else 0
                self._safe_create_item(
                    self.canvas.create_oval,
                    cx - pupil_size // 4 - highlight_size // 2 + offset,
                    cy - pupil_size // 4 - highlight_size // 2,
                    cx - pupil_size // 4 + highlight_size // 2 + offset,
                    cy - pupil_size // 4 + highlight_size // 2,
                    fill=COLOR_WHITE, outline="",
                )

                # 第二个小高光
                small_highlight = highlight_size * 0.5
                self._safe_create_item(
                    self.canvas.create_oval,
                    cx + pupil_size // 4 - small_highlight // 2,
                    cy + pupil_size // 4 - small_highlight // 2,
                    cx + pupil_size // 4 + small_highlight // 2,
                    cy + pupil_size // 4 + small_highlight // 2,
                    fill="#eeeeee", outline="",
                )

        except Exception as e:
            log_exception(logger, "绘制眼睛异常", e)

    def _draw_nose(self, cx: int, cy: int, width: int, height: int) -> None:
        """绘制鼻子

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
            width: 宽度
            height: 高度
        """
        if not self._validate_part_coords(cx, cy, width, height, "nose"):
            return

        try:
            # 鼻子主体
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_NOSE_PINK, outline=COLOR_DARK_GRAY, width=1,
            )
            # 鼻子高光
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 4, cy - height // 3,
                cx, cy - height // 6,
                fill="#ff8ec4", outline="",
            )
        except Exception as e:
            log_exception(logger, "绘制鼻子异常", e)

    def _draw_tail(self, cx: int, cy: int, width: int, height: int, angle: float) -> None:
        """绘制尾巴

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
            width: 宽度
            height: 高度
            angle: 角度
        """
        if not self._validate_part_coords(cx, cy, width, height, "tail"):
            return

        try:
            # 使用弧形绘制弯曲的尾巴
            self._safe_create_item(
                self.canvas.create_arc,
                cx - width, cy - height,
                cx + width, cy + height,
                start=0, extent=angle,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY, width=1,
            )

            # 尾巴尖（浅色）
            tip_size = 4
            tip_x = cx + width * 0.7
            tip_y = cy - height * 0.5
            self._safe_create_item(
                self.canvas.create_oval,
                tip_x - tip_size, tip_y - tip_size,
                tip_x + tip_size, tip_y + tip_size,
                fill="#2a2a2a", outline="",
            )

        except Exception as e:
            log_exception(logger, "绘制尾巴异常", e)

    def _draw_leg(self, cx: int, cy: int, width: int, height: int,
                  angle: float, is_front: bool) -> None:
        """绘制腿

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
            width: 宽度
            height: 高度
            angle: 角度
            is_front: 是否为前腿
        """
        if not self._validate_part_coords(cx, cy, width, height, "leg"):
            return

        try:
            # 腿主体
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_BLACK, outline=COLOR_DARK_GRAY, width=1,
            )

            # 爪子（更圆润）
            paw_size = width * 0.9
            paw_y = cy + height // 2 - paw_size // 2
            self._safe_create_item(
                self.canvas.create_oval,
                cx - paw_size, paw_y - paw_size // 2,
                cx + paw_size, paw_y + paw_size // 2,
                fill="#2a2a2a", outline=COLOR_DARK_GRAY, width=1,
            )
            # 爪子高光
            self._safe_create_item(
                self.canvas.create_oval,
                cx - paw_size // 2, paw_y - paw_size // 3,
                cx, paw_y,
                fill="#333333", outline="",
            )

        except Exception as e:
            log_exception(logger, "绘制腿部异常", e)

    def _draw_spots(self, cx: int, cy: int) -> None:
        """绘制装饰斑点

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
        """
        try:
            # 背上的斑点（3个，增加层次感）
            spots = [(cx - 5, cy - 3, 4), (cx + 8, cy + 2, 3), (cx - 2, cy + 5, 2)]
            for sx, sy, size in spots:
                self._safe_create_item(
                    self.canvas.create_oval,
                    sx - size, sy - size,
                    sx + size, sy + size,
                    fill="#2a2a2a", outline="",
                )
        except Exception as e:
            log_exception(logger, "绘制斑点异常", e)

    def _draw_blush(self, cx: int, cy: int, head_w: int, head_h: int) -> None:
        """绘制腮红（可爱装饰）

        在脸颊两侧添加半透明粉色腮红。

        Args:
            cx: 头部中心 x 坐标
            cy: 头部中心 y 坐标
            head_w: 头部宽度
            head_h: 头部高度
        """
        try:
            blush_size = 4
            blush_y = cy - head_h // 6
            # 左腮红
            left_blush_x = cx - head_w // 3
            self._safe_create_item(
                self.canvas.create_oval,
                left_blush_x - blush_size, blush_y - blush_size // 2,
                left_blush_x + blush_size, blush_y + blush_size // 2,
                fill="#ff9999", outline="", stipple="gray50",
            )
            # 右腮红
            right_blush_x = cx + head_w // 3
            self._safe_create_item(
                self.canvas.create_oval,
                right_blush_x - blush_size, blush_y - blush_size // 2,
                right_blush_x + blush_size, blush_y + blush_size // 2,
                fill="#ff9999", outline="", stipple="gray50",
            )
        except Exception as e:
            log_exception(logger, "绘制腮红异常", e)

    def _draw_tongue(self, cx: int, cy: int, width: int, height: int) -> None:
        """绘制舌头

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
            width: 宽度
            height: 高度
        """
        if not self._validate_part_coords(cx, cy, width, height, "tongue"):
            return

        try:
            # 舌头主体
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill=COLOR_PINK, outline=COLOR_DARK_GRAY, width=1,
            )
            # 舌头高光
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 4, cy - height // 3,
                cx + width // 4, cy,
                fill="#ffc0cb", outline="",
            )
        except Exception as e:
            log_exception(logger, "绘制舌头异常", e)

    def _draw_mouth_open(self, cx: int, cy: int, width: int, height: int) -> None:
        """绘制张开的嘴巴（打哈欠）

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
            width: 宽度
            height: 高度
        """
        if not self._validate_part_coords(cx, cy, width, height, "mouth"):
            return

        try:
            self._safe_create_item(
                self.canvas.create_oval,
                cx - width // 2, cy - height // 2,
                cx + width // 2, cy + height // 2,
                fill="#4a0000", outline=COLOR_DARK_GRAY, width=1,
            )
        except Exception as e:
            log_exception(logger, "绘制嘴巴异常", e)

    def _draw_zzz(self, cx: int, cy: int, width: int, height: int) -> None:
        """绘制睡觉的 Zzz 符号

        Args:
            cx: 中心 x 坐标
            cy: 中心 y 坐标
            width: 宽度
            height: 高度
        """
        if not self._validate_part_coords(cx, cy, width, height, "zzz"):
            return

        try:
            # 使用文字绘制
            self._safe_create_item(
                self.canvas.create_text,
                cx, cy,
                text="Z",
                fill="#666666",
                font=("Arial", max(8, int(width * 0.8)), "bold"),
            )
            self._safe_create_item(
                self.canvas.create_text,
                cx + width * 0.6, cy - height * 0.4,
                text="z",
                fill="#888888",
                font=("Arial", max(6, int(width * 0.5)), "bold"),
            )
            self._safe_create_item(
                self.canvas.create_text,
                cx + width * 1.0, cy - height * 0.7,
                text="z",
                fill="#aaaaaa",
                font=("Arial", max(5, int(width * 0.3)), "bold"),
            )
        except Exception as e:
            log_exception(logger, "绘制 Zzz 异常", e)

    def update_animation(self, state: PuppyState) -> None:
        """更新动画

        Args:
            state: 新状态
        """
        if not self._check_canvas():
            return

        if not isinstance(state, PuppyState):
            logger.warning(f"无效的状态类型: {type(state)}")
            return

        try:
            self.animation_manager.set_state(state)
            frame = self.animation_manager.get_current_frame()
            self.clear_puppy()
            self._draw_frame(frame)
        except Exception as e:
            log_exception(logger, f"更新动画异常: {state.name}", e)

    def advance_frame(self) -> None:
        """推进动画帧"""
        if not self._check_canvas():
            return

        try:
            self.animation_manager.advance_frame()
            frame = self.animation_manager.get_current_frame()
            self.clear_puppy()
            self._draw_frame(frame)
        except Exception as e:
            log_exception(logger, "推进动画帧异常", e)

    def clear_puppy(self) -> None:
        """清除小黑狗"""
        if not self._check_canvas():
            self.current_items.clear()
            return

        for item in self.current_items:
            try:
                self.canvas.delete(item)
            except tk.TclError:
                pass  # 项目可能已被删除
            except Exception as e:
                logger.debug(f"删除 Canvas 项目异常: {e}")

        self.current_items.clear()

    def set_position(self, x: int, y: int) -> None:
        """设置绘制位置

        Args:
            x: x 坐标
            y: y 坐标
        """
        try:
            self.center_x = int(x)
            self.center_y = int(y)
        except (ValueError, TypeError) as e:
            logger.warning(f"设置绘制位置参数错误: x={x}, y={y}, 错误: {e}")

    def get_animation_manager(self) -> AnimationManager:
        """获取动画管理器

        Returns:
            AnimationManager 实例
        """
        return self.animation_manager

    def invalidate_canvas(self) -> None:
        """标记 Canvas 为无效（窗口销毁时调用）"""
        self._canvas_valid = False
        logger.debug("Canvas 已标记为无效")
