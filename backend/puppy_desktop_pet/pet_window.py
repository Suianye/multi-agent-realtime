"""
窗口管理模块
管理透明窗口、拖拽移动和气泡消息
包含完整的错误处理和边界验证

增强功能:
    1. 窗口生命周期安全检查
    2. 拖拽边界保护（防飞出屏幕）
    3. 气泡消息消毒
    4. 位置验证与自动修正
    5. 资源泄漏防护
"""
import tkinter as tk
from typing import Optional
from config import (CANVAS_WIDTH, CANVAS_HEIGHT, WINDOW_TITLE,
                    BUBBLE_FONT, BUBBLE_BG, BUBBLE_FG, BUBBLE_DURATION,
                    validate_position, validate_color, get_safe_screen_position)
from logger import get_logger, log_exception

# 模块日志记录器
logger = get_logger("pet_window")


class PetWindow:
    """宠物窗口管理器

    负责：
    1. 创建和管理透明窗口
    2. 窗口位置和大小控制
    3. 拖拽移动
    4. 气泡消息显示

    包含完整的错误处理和边界验证。
    """

    def __init__(self, root: tk.Tk):
        """初始化宠物窗口

        Args:
            root: tkinter 根窗口

        Raises:
            RuntimeError: 窗口创建失败时抛出
        """
        if not isinstance(root, tk.Tk):
            raise TypeError(f"root 必须是 tk.Tk 实例，实际为 {type(root)}")

        self.root = root
        self._destroyed = False
        self._bubble_timer: Optional[str] = None

        try:
            # 创建顶级窗口
            self.window = tk.Toplevel(root)
            self.window.title(WINDOW_TITLE)
            self.window.overrideredirect(True)  # 去掉标题栏
            self.window.attributes('-topmost', True)  # 始终在最前

            # 设置透明背景（Windows）
            try:
                self.window.attributes('-transparentcolor', 'white')
                logger.debug("透明背景已启用")
            except Exception as e:
                logger.debug(f"透明背景不可用（非 Windows 系统）: {e}")

            # 创建主框架
            self.frame = tk.Frame(self.window, bg='white')
            self.frame.pack()

            # 气泡容器框架（用于实现阴影效果）
            self._bubble_frame = tk.Frame(self.frame, bg='white')

            # 气泡阴影（偏移2像素的深色背景标签）
            self._bubble_shadow = tk.Label(
                self._bubble_frame,
                text="",
                font=BUBBLE_FONT,
                bg="#cccccc",
                fg="#cccccc",
                padx=9,
                pady=5,
                relief=tk.FLAT,
                borderwidth=0,
            )

            # 气泡标签（更精美的样式）
            self.bubble_label = tk.Label(
                self._bubble_frame,
                text="",
                font=("微软雅黑", 9, "bold"),
                bg="#fff8f0",
                fg="#5a3e28",
                padx=10,
                pady=5,
                relief=tk.SOLID,
                borderwidth=1,
                highlightbackground="#e8c9a0",
                highlightthickness=1,
            )
            self.bubble_visible = False

            # 创建 Canvas
            self.canvas = tk.Canvas(
                self.frame,
                width=CANVAS_WIDTH,
                height=CANVAS_HEIGHT,
                bg='white',
                highlightthickness=0,
            )
            self.canvas.pack()

            # 拖拽状态
            self.dragging = False
            self.drag_start_x = 0
            self.drag_start_y = 0
            self.x = 0
            self.y = 0

            # 窗口尺寸
            self.width = CANVAS_WIDTH
            self.height = CANVAS_HEIGHT

            # 绑定拖拽事件
            self.canvas.bind('<Button-1>', self._on_drag_start)
            self.canvas.bind('<B1-Motion>', self._on_drag_move)
            self.canvas.bind('<ButtonRelease-1>', self._on_drag_end)

            # 绑定窗口销毁事件
            self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)

            logger.info("宠物窗口已创建")

        except Exception as e:
            log_exception(logger, "创建宠物窗口失败", e)
            raise RuntimeError(f"无法创建宠物窗口: {e}") from e

    def _check_not_destroyed(self) -> bool:
        """检查窗口是否已销毁

        Returns:
            窗口是否可用
        """
        if self._destroyed:
            logger.warning("尝试操作已销毁的窗口")
            return False
        return True

    def _on_window_close(self) -> None:
        """窗口关闭事件处理"""
        logger.debug("窗口关闭事件触发")
        self._cleanup()

    def _cleanup(self) -> None:
        """清理资源"""
        if self._destroyed:
            return

        self._destroyed = True

        # 取消定时器
        self._cancel_bubble_timer()

        # 销毁窗口
        try:
            if self.window and self.window.winfo_exists():
                self.window.destroy()
                logger.debug("窗口已销毁")
        except Exception as e:
            logger.debug(f"销毁窗口时出错（可能已销毁）: {e}")

        logger.info("窗口资源已清理")

    def _cancel_bubble_timer(self) -> None:
        """安全取消气泡定时器"""
        if self._bubble_timer is not None:
            try:
                self.root.after_cancel(self._bubble_timer)
            except (ValueError, tk.TclError) as e:
                logger.debug(f"取消气泡定时器失败: {e}")
            finally:
                self._bubble_timer = None

    def _on_drag_start(self, event) -> None:
        """拖拽开始

        Args:
            event: tkinter 事件
        """
        if not self._check_not_destroyed():
            return

        try:
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            logger.debug(f"拖拽开始: ({event.x}, {event.y})")
        except Exception as e:
            log_exception(logger, "拖拽开始处理异常", e)
            self.dragging = False

    def _on_drag_move(self, event) -> None:
        """拖拽移动

        Args:
            event: tkinter 事件
        """
        if not self._check_not_destroyed() or not self.dragging:
            return

        try:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y

            # 限制单次移动距离，防止窗口飞出屏幕
            max_move = 100
            dx = max(-max_move, min(max_move, dx))
            dy = max(-max_move, min(max_move, dy))

            new_x = self.x + dx
            new_y = self.y + dy

            # 边界检查：使用安全位置函数
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            # 使用双重验证确保安全
            new_x, new_y = validate_position(new_x, new_y, screen_width, screen_height)
            new_x, new_y = get_safe_screen_position(new_x, new_y, self.width, self.height)

            self.x = new_x
            self.y = new_y
            self.window.geometry(f'+{self.x}+{self.y}')

            # 更新拖拽起始位置，防止累积偏移
            self.drag_start_x = event.x
            self.drag_start_y = event.y

        except tk.TclError as e:
            logger.debug(f"拖拽移动 Tcl 错误: {e}")
            self.dragging = False
        except Exception as e:
            log_exception(logger, "拖拽移动处理异常", e)
            self.dragging = False

    def _on_drag_end(self, event) -> None:
        """拖拽结束

        Args:
            event: tkinter 事件
        """
        if not self._check_not_destroyed():
            return

        try:
            self.dragging = False
            logger.debug(f"拖拽结束: 位置 ({self.x}, {self.y})")
        except Exception as e:
            log_exception(logger, "拖拽结束处理异常", e)

    def show_bubble(self, message: str, duration: int = BUBBLE_DURATION) -> None:
        """显示气泡消息

        Args:
            message: 消息内容
            duration: 显示时长（毫秒）
        """
        if not self._check_not_destroyed():
            return

        # 输入验证与消毒
        if not isinstance(message, str):
            logger.warning(f"气泡消息类型错误: {type(message)}，转换为字符串")
            try:
                message = str(message)
            except Exception:
                logger.debug("消息转换失败，跳过显示")
                return

        if not message or not message.strip():
            logger.debug("空消息，跳过显示")
            return

        # 消毒消息内容（移除控制字符）
        message = ''.join(
            char for char in message
            if char in ('\n', '\r', '\t') or (ord(char) >= 32)
        )

        if not message:
            return

        # 验证持续时间
        if not isinstance(duration, (int, float)) or duration <= 0:
            logger.warning(f"气泡持续时间无效: {duration}，使用默认值")
            duration = BUBBLE_DURATION

        duration = int(max(500, min(30000, duration)))  # 限制在 0.5s - 30s

        try:
            # 取消之前的定时器
            self._cancel_bubble_timer()

            # 截断过长的消息
            max_length = 50
            display_message = message[:max_length] + "..." if len(message) > max_length else message

            # 转义特殊字符（防止 Tk 解析错误）
            display_message = display_message.replace('{', '\\{').replace('}', '\\}')

            # 显示气泡（带阴影效果）
            self._bubble_shadow.config(text=display_message)
            self.bubble_label.config(text=display_message)
            self._bubble_frame.pack(before=self.canvas, pady=(0, 2))
            self._bubble_shadow.pack(side=tk.LEFT, padx=(2, 0), pady=(2, 0))
            self.bubble_label.pack(side=tk.LEFT, padx=(0, 0), pady=(0, 2))
            self.bubble_visible = True

            # 设置自动隐藏
            self._bubble_timer = self.root.after(duration, self._hide_bubble_safe)

            logger.debug(f"显示气泡: '{display_message}' ({duration}ms)")

        except tk.TclError as e:
            logger.warning(f"显示气泡 Tcl 错误: {e}")
            self.bubble_visible = False
        except Exception as e:
            log_exception(logger, "显示气泡异常", e)
            self.bubble_visible = False

    def _hide_bubble_safe(self) -> None:
        """安全隐藏气泡（定时器回调）"""
        try:
            self.hide_bubble()
        except Exception as e:
            log_exception(logger, "隐藏气泡异常", e)

    def hide_bubble(self) -> None:
        """隐藏气泡"""
        if not self._check_not_destroyed():
            return

        try:
            self._cancel_bubble_timer()
            self.bubble_label.pack_forget()
            self._bubble_shadow.pack_forget()
            self._bubble_frame.pack_forget()
            self.bubble_visible = False
        except tk.TclError as e:
            logger.debug(f"隐藏气泡 Tcl 错误: {e}")
        except Exception as e:
            log_exception(logger, "隐藏气泡异常", e)

    def set_position(self, x: int, y: int) -> None:
        """设置窗口位置

        Args:
            x: x 坐标
            y: y 坐标
        """
        if not self._check_not_destroyed():
            return

        # 输入验证
        try:
            x = int(x)
            y = int(y)
        except (ValueError, TypeError) as e:
            logger.warning(f"位置参数类型错误: x={x}, y={y}, 错误: {e}")
            return

        # 边界检查（双重验证）
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x, y = validate_position(x, y, screen_width, screen_height)
        x, y = get_safe_screen_position(x, y, self.width, self.height)

        try:
            self.x = x
            self.y = y
            self.window.geometry(f'+{x}+{y}')
        except tk.TclError as e:
            logger.warning(f"设置窗口位置 Tcl 错误: {e}")
        except Exception as e:
            log_exception(logger, "设置窗口位置异常", e)

    def get_position(self) -> tuple:
        """获取窗口位置

        Returns:
            (x, y) 坐标元组
        """
        return (self.x, self.y)

    def get_canvas(self) -> tk.Canvas:
        """获取 Canvas

        Returns:
            Canvas 对象
        """
        return self.canvas

    def get_window(self) -> tk.Toplevel:
        """获取窗口对象

        Returns:
            Toplevel 窗口对象
        """
        return self.window

    def set_visible(self, visible: bool) -> None:
        """设置窗口可见性

        Args:
            visible: 是否可见
        """
        if not self._check_not_destroyed():
            return

        try:
            if visible:
                self.window.deiconify()
            else:
                self.window.withdraw()
        except tk.TclError as e:
            logger.warning(f"设置可见性 Tcl 错误: {e}")
        except Exception as e:
            log_exception(logger, "设置可见性异常", e)

    def set_topmost(self, topmost: bool) -> None:
        """设置窗口是否始终在最前

        Args:
            topmost: 是否始终在最前
        """
        if not self._check_not_destroyed():
            return

        try:
            self.window.attributes('-topmost', topmost)
        except Exception as e:
            log_exception(logger, "设置 topmost 异常", e)

    def set_alpha(self, alpha: float) -> None:
        """设置窗口透明度

        Args:
            alpha: 透明度 (0.0 - 1.0)
        """
        if not self._check_not_destroyed():
            return

        # 验证透明度范围
        if not isinstance(alpha, (int, float)):
            logger.warning(f"透明度类型错误: {type(alpha)}")
            return

        alpha = max(0.0, min(1.0, float(alpha)))

        try:
            self.window.attributes('-alpha', alpha)
        except Exception as e:
            log_exception(logger, "设置透明度异常", e)

    def center_on_screen(self) -> None:
        """将窗口居中到屏幕"""
        if not self._check_not_destroyed():
            return

        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - self.width) // 2
            y = (screen_height - self.height) // 2
            self.set_position(x, y)
        except Exception as e:
            log_exception(logger, "居中窗口异常", e)

    def update(self) -> None:
        """更新窗口"""
        if not self._check_not_destroyed():
            return

        try:
            self.window.update()
        except tk.TclError as e:
            logger.debug(f"窗口更新 Tcl 错误: {e}")
        except Exception as e:
            log_exception(logger, "窗口更新异常", e)

    def destroy(self) -> None:
        """销毁窗口"""
        self._cleanup()

    def is_destroyed(self) -> bool:
        """检查窗口是否已销毁

        Returns:
            窗口是否已销毁
        """
        return self._destroyed
