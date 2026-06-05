"""
事件路由模块
管理所有用户交互事件的分发和处理

功能说明:
    1. 将 tkinter 原生事件转换为自定义 Event 对象
    2. 支持事件过滤器（阻止事件传播）
    3. 支持事件处理器优先级
    4. 区分单击/双击/拖拽的智能识别
    5. 提供事件传播控制（stop_propagation）
"""
import tkinter as tk
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from enum import Enum, auto

from logger import get_logger

logger = get_logger("event_router")


# ──────────────────────────────────────────────
# 事件类型枚举
# ──────────────────────────────────────────────

class EventType(Enum):
    """事件类型枚举"""
    CLICK = auto()          # 单击
    DOUBLE_CLICK = auto()   # 双击
    RIGHT_CLICK = auto()    # 右键点击
    DRAG_START = auto()     # 拖拽开始
    DRAG_MOVE = auto()      # 拖拽中
    DRAG_END = auto()       # 拖拽结束
    HOVER_ENTER = auto()    # 鼠标进入
    HOVER_LEAVE = auto()    # 鼠标离开
    KEY_PRESS = auto()      # 按键


# ──────────────────────────────────────────────
# 事件数据类
# ──────────────────────────────────────────────

class Event:
    """事件数据类

    Attributes:
        type: 事件类型
        x: 鼠标 x 坐标（相对于 Canvas）
        y: 鼠标 y 坐标（相对于 Canvas）
        button: 鼠标按键编号（1=左键, 2=中键, 3=右键）
        key: 按键字符（仅 KEY_PRESS 事件有效）
        widget: 触发事件的 tkinter 控件
        timestamp: 事件发生的时间戳
        _propagation_stopped: 是否已阻止事件继续传播
    """

    __slots__ = ("type", "x", "y", "button", "key", "widget",
                 "timestamp", "_propagation_stopped")

    def __init__(self, event_type: EventType, x: int = 0, y: int = 0,
                 button: int = 0, key: str = "", widget: tk.Widget = None):
        self.type = event_type
        self.x = x
        self.y = y
        self.button = button
        self.key = key
        self.widget = widget
        self.timestamp: float = time.time()
        self._propagation_stopped = False

    def stop_propagation(self):
        """阻止事件继续传播到后续处理器

        调用此方法后，当前事件类型的后续处理器将不会被执行。
        """
        self._propagation_stopped = True
        logger.debug("事件传播已停止: %s", self.type.name)

    def __repr__(self) -> str:
        return (f"Event({self.type.name}, x={self.x}, y={self.y}, "
                f"button={self.button}, key='{self.key}')")


# ──────────────────────────────────────────────
# 事件处理器包装
# ──────────────────────────────────────────────

@dataclass
class HandlerEntry:
    """处理器条目，用于支持优先级排序

    Attributes:
        handler: 处理函数
        priority: 优先级（数值越小优先级越高，默认 100）
    """
    handler: Callable
    priority: int = 100

    def __lt__(self, other: 'HandlerEntry') -> bool:
        return self.priority < other.priority


# ──────────────────────────────────────────────
# 事件路由器
# ──────────────────────────────────────────────

class EventRouter:
    """事件路由器

    负责将 tkinter 原生事件转换为自定义事件，并分发到对应的处理器。
    支持事件过滤、优先级处理、传播控制等功能。

    使用示例:
        router = EventRouter(canvas)
        router.on(EventType.CLICK, my_handler, priority=10)
        router.add_filter(my_filter_func)
    """

    def __init__(self, canvas: tk.Canvas):
        if not isinstance(canvas, tk.Canvas):
            raise TypeError(f"canvas 必须是 tk.Canvas 实例，实际为 {type(canvas)}")

        self.canvas = canvas
        self._handlers: Dict[EventType, List[HandlerEntry]] = {}
        self._filters: List[Callable] = []
        self._dragging = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._drag_threshold = 5      # 拖拽阈值（像素）
        self._click_timer = None
        self._double_click_delay = 300  # 双击延迟（毫秒）
        self._destroyed = False
        self._emit_depth = 0            # 防止递归触发
        self._max_emit_depth = 10       # 最大递归深度

        # 统计信息
        self._event_count: Dict[EventType, int] = {}
        self._error_count: int = 0

        # 绑定原生事件
        try:
            self._bind_native_events()
            logger.info("事件路由器初始化完成")
        except Exception as e:
            logger.error("事件路由器初始化失败: %s", e, exc_info=True)
            raise RuntimeError(f"无法初始化事件路由器: {e}") from e

    # ──────────────────────────────────────────
    # 事件绑定
    # ──────────────────────────────────────────

    def _bind_native_events(self):
        """绑定 tkinter 原生事件到路由器"""
        bindings = {
            '<Button-1>': self._on_button_press,
            '<B1-Motion>': self._on_motion,
            '<ButtonRelease-1>': self._on_button_release,
            '<Button-3>': self._on_right_click,
            '<Double-Button-1>': self._on_double_click,
            '<Enter>': self._on_enter,
            '<Leave>': self._on_leave,
            '<Key>': self._on_key_press,
        }
        for sequence, callback in bindings.items():
            try:
                self.canvas.bind(sequence, callback)
            except tk.TclError as e:
                logger.warning("绑定事件失败 %s: %s", sequence, e)
        logger.debug("已绑定 %d 个原生事件", len(bindings))

    def _check_alive(self) -> bool:
        """检查路由器是否可用

        Returns:
            路由器是否可用
        """
        if self._destroyed:
            logger.warning("尝试操作已销毁的事件路由器")
            return False
        return True

    # ──────────────────────────────────────────
    # 处理器注册
    # ──────────────────────────────────────────

    def on(self, event_type: EventType, handler: Callable, priority: int = 100):
        """注册事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数，接收 Event 对象作为参数
            priority: 优先级（数值越小越先执行，默认 100）
        """
        if not self._check_alive():
            return

        if not isinstance(event_type, EventType):
            logger.warning("注册处理器: 无效的事件类型 %s", event_type)
            return

        if not callable(handler):
            logger.warning("注册的处理器不可调用: %s", handler)
            return

        if not isinstance(priority, int):
            logger.warning("优先级类型错误: %s，使用默认值 100", type(priority))
            priority = 100

        try:
            if event_type not in self._handlers:
                self._handlers[event_type] = []

            entry = HandlerEntry(handler=handler, priority=priority)
            self._handlers[event_type].append(entry)
            # 按优先级排序
            self._handlers[event_type].sort()
            logger.debug("注册处理器: %s (优先级: %d)", event_type.name, priority)
        except Exception as e:
            logger.error("注册处理器异常: %s - %s", event_type.name, e)

    def off(self, event_type: EventType, handler: Callable = None):
        """移除事件处理器

        Args:
            event_type: 事件类型
            handler: 要移除的处理函数，None 则移除该类型所有处理器
        """
        if event_type not in self._handlers:
            return

        if handler is None:
            self._handlers[event_type] = []
            logger.debug("已移除 %s 的所有处理器", event_type.name)
        else:
            self._handlers[event_type] = [
                entry for entry in self._handlers[event_type]
                if entry.handler != handler
            ]
            logger.debug("已移除 %s 的指定处理器", event_type.name)

    # ──────────────────────────────────────────
    # 事件过滤器
    # ──────────────────────────────────────────

    def add_filter(self, filter_func: Callable) -> None:
        """添加事件过滤器

        过滤器函数接收 Event 对象，返回 False 时事件将被阻止传播。

        Args:
            filter_func: 过滤函数，返回 True 允许传播，False 阻止
        """
        if not callable(filter_func):
            logger.warning("添加的过滤器不可调用: %s", filter_func)
            return
        self._filters.append(filter_func)
        logger.debug("添加事件过滤器 (共 %d 个)", len(self._filters))

    def remove_filter(self, filter_func: Callable) -> None:
        """移除事件过滤器

        Args:
            filter_func: 要移除的过滤函数
        """
        if filter_func in self._filters:
            self._filters.remove(filter_func)
            logger.debug("已移除事件过滤器")

    # ──────────────────────────────────────────
    # 事件分发
    # ──────────────────────────────────────────

    def _emit(self, event: Event) -> None:
        """触发事件

        处理流程:
            1. 递归深度检查（防止无限递归）
            2. 经过过滤器检查
            3. 按优先级顺序分发到处理器
            4. 支持 stop_propagation() 中断传播

        Args:
            event: 要触发的事件对象
        """
        if not self._check_alive():
            return

        # 递归深度保护
        self._emit_depth += 1
        if self._emit_depth > self._max_emit_depth:
            logger.error("事件触发递归过深 (%d)，中止: %s", self._emit_depth, event.type.name)
            self._emit_depth -= 1
            return

        try:
            # 统计
            self._event_count[event.type] = self._event_count.get(event.type, 0) + 1

            # 过滤器检查
            for filter_func in self._filters:
                try:
                    if not filter_func(event):
                        logger.debug("事件被过滤器阻止: %s", event.type.name)
                        return
                except Exception as e:
                    logger.warning("过滤器执行异常: %s - %s", event.type.name, e)

            # 分发到处理器（按优先级顺序）
            entries = self._handlers.get(event.type, [])
            for entry in entries:
                if event._propagation_stopped:
                    logger.debug("事件传播已停止，跳过后续处理器: %s", event.type.name)
                    break
                try:
                    entry.handler(event)
                except Exception as e:
                    self._error_count += 1
                    logger.error("事件处理错误 [%s]: %s", event.type.name, e, exc_info=True)

                    # 连续错误过多时警告
                    if self._error_count % 10 == 0:
                        logger.warning("事件处理已累计 %d 次错误", self._error_count)
        finally:
            self._emit_depth -= 1

    # ──────────────────────────────────────────
    # 原生事件处理: 鼠标按下
    # ──────────────────────────────────────────

    def _on_button_press(self, tk_event: tk.Event) -> None:
        """处理鼠标按下事件

        逻辑:
            - 记录按下位置
            - 设置延迟定时器用于区分单击和双击
        """
        if not self._check_alive():
            return

        try:
            self._drag_start_x = tk_event.x
            self._drag_start_y = tk_event.y
            self._dragging = False

            # 使用 after 实现单击/双击区分
            self._cancel_click_timer()

            self._click_timer = self.canvas.after(
                self._double_click_delay,
                lambda: self._handle_single_click(tk_event)
            )
        except tk.TclError as e:
            logger.debug("鼠标按下处理 Tcl 错误: %s", e)
        except Exception as e:
            logger.error("鼠标按下处理异常: %s", e, exc_info=True)

    def _cancel_click_timer(self) -> None:
        """安全取消单击定时器"""
        if self._click_timer is not None:
            try:
                self.canvas.after_cancel(self._click_timer)
            except (ValueError, tk.TclError) as e:
                logger.debug("取消单击定时器失败: %s", e)
            finally:
                self._click_timer = None

    def _handle_single_click(self, tk_event: tk.Event) -> None:
        """处理单击事件（延迟后确认）

        只有在没有发生拖拽的情况下才触发单击事件。
        """
        self._click_timer = None

        if not self._check_alive():
            return

        try:
            if not self._dragging:
                event = Event(
                    EventType.CLICK,
                    x=tk_event.x,
                    y=tk_event.y,
                    button=1,
                    widget=tk_event.widget
                )
                self._emit(event)
        except Exception as e:
            logger.error("单击处理异常: %s", e, exc_info=True)

    # ──────────────────────────────────────────
    # 原生事件处理: 鼠标移动
    # ──────────────────────────────────────────

    def _on_motion(self, tk_event: tk.Event) -> None:
        """处理鼠标移动事件

        逻辑:
            - 计算与按下位置的偏移
            - 超过阈值时切换为拖拽模式
            - 拖拽模式下持续触发 DRAG_MOVE
        """
        if not self._check_alive():
            return

        try:
            dx = tk_event.x - self._drag_start_x
            dy = tk_event.y - self._drag_start_y

            if not self._dragging and (abs(dx) > self._drag_threshold or abs(dy) > self._drag_threshold):
                self._dragging = True
                # 取消待处理的单击
                self._cancel_click_timer()
                # 触发拖拽开始
                event = Event(EventType.DRAG_START, x=self._drag_start_x, y=self._drag_start_y)
                self._emit(event)

            if self._dragging:
                event = Event(EventType.DRAG_MOVE, x=tk_event.x, y=tk_event.y)
                self._emit(event)
        except Exception as e:
            logger.error("鼠标移动处理异常: %s", e, exc_info=True)
            self._dragging = False

    # ──────────────────────────────────────────
    # 原生事件处理: 鼠标释放
    # ──────────────────────────────────────────

    def _on_button_release(self, tk_event: tk.Event) -> None:
        """处理鼠标释放事件

        如果处于拖拽状态，触发 DRAG_END 事件。
        """
        if not self._check_alive():
            return

        try:
            if self._dragging:
                self._dragging = False
                event = Event(EventType.DRAG_END, x=tk_event.x, y=tk_event.y)
                self._emit(event)
        except Exception as e:
            logger.error("鼠标释放处理异常: %s", e, exc_info=True)
            self._dragging = False

    # ──────────────────────────────────────────
    # 原生事件处理: 右键
    # ──────────────────────────────────────────

    def _on_right_click(self, tk_event: tk.Event) -> None:
        """处理右键点击事件"""
        if not self._check_alive():
            return

        try:
            event = Event(
                EventType.RIGHT_CLICK,
                x=tk_event.x,
                y=tk_event.y,
                button=3,
                widget=tk_event.widget
            )
            self._emit(event)
        except Exception as e:
            logger.error("右键点击处理异常: %s", e, exc_info=True)

    # ──────────────────────────────────────────
    # 原生事件处理: 双击
    # ──────────────────────────────────────────

    def _on_double_click(self, tk_event: tk.Event) -> None:
        """处理双击事件

        双击时取消待处理的单击定时器，避免重复触发。
        """
        if not self._check_alive():
            return

        try:
            self._cancel_click_timer()

            event = Event(
                EventType.DOUBLE_CLICK,
                x=tk_event.x,
                y=tk_event.y,
                button=1,
                widget=tk_event.widget
            )
            self._emit(event)
        except Exception as e:
            logger.error("双击处理异常: %s", e, exc_info=True)

    # ──────────────────────────────────────────
    # 原生事件处理: 悬停
    # ──────────────────────────────────────────

    def _on_enter(self, tk_event: tk.Event) -> None:
        """处理鼠标进入事件"""
        event = Event(EventType.HOVER_ENTER, x=tk_event.x, y=tk_event.y)
        self._emit(event)

    def _on_leave(self, tk_event: tk.Event) -> None:
        """处理鼠标离开事件"""
        event = Event(EventType.HOVER_LEAVE)
        self._emit(event)

    # ──────────────────────────────────────────
    # 原生事件处理: 按键
    # ──────────────────────────────────────────

    def _on_key_press(self, tk_event: tk.Event) -> None:
        """处理按键事件"""
        event = Event(EventType.KEY_PRESS, key=tk_event.char)
        self._emit(event)

    # ──────────────────────────────────────────
    # 状态查询与配置
    # ──────────────────────────────────────────

    def is_dragging(self) -> bool:
        """是否正在拖拽"""
        return self._dragging

    def set_drag_threshold(self, threshold: int) -> None:
        """设置拖拽阈值（像素）

        Args:
            threshold: 阈值，必须为正整数
        """
        if not isinstance(threshold, int) or threshold <= 0:
            logger.warning("无效的拖拽阈值: %s，使用默认值 5", threshold)
            return
        self._drag_threshold = threshold
        logger.debug("拖拽阈值设置为: %d", threshold)

    def set_double_click_delay(self, delay: int) -> None:
        """设置双击延迟（毫秒）

        Args:
            delay: 延迟时间，必须为正整数
        """
        if not isinstance(delay, int) or delay <= 0:
            logger.warning("无效的双击延迟: %s，使用默认值 300", delay)
            return
        self._double_click_delay = delay
        logger.debug("双击延迟设置为: %d ms", delay)

    def get_event_stats(self) -> Dict[str, int]:
        """获取事件统计信息

        Returns:
            各类型事件的触发次数
        """
        return {et.name: count for et, count in self._event_count.items()}

    def reset_stats(self) -> None:
        """重置事件统计"""
        self._event_count.clear()
        self._error_count = 0

    def get_error_count(self) -> int:
        """获取错误计数

        Returns:
            事件处理错误总数
        """
        return self._error_count

    def destroy(self) -> None:
        """销毁事件路由器，清理资源"""
        if self._destroyed:
            return

        self._destroyed = True

        # 取消定时器
        self._cancel_click_timer()

        # 清理处理器和过滤器
        self._handlers.clear()
        self._filters.clear()

        # 重置状态
        self._dragging = False

        logger.info("事件路由器已销毁 (总事件: %d, 错误: %d)",
                     sum(self._event_count.values()), self._error_count)
