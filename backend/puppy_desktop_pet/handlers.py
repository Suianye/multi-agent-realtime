"""
事件处理器模块
定义各种事件的具体处理逻辑

处理器说明:
    - PuppyEventHandlers: 小黑狗交互事件（点击、拖拽、悬停）
    - WindowEventHandlers: 窗口级事件（关闭、最小化）
    - KeyboardEventHandlers: 键盘快捷键事件
    - ContextMenuHandler: 右键上下文菜单
"""
import tkinter as tk
from typing import Optional, Callable, Dict
from dataclasses import dataclass

from event_router import Event, EventType, EventRouter
from animations import PuppyState
from config import WALK_SPEED, CANVAS_WIDTH
from logger import get_logger

logger = get_logger("handlers")


# ──────────────────────────────────────────────
# 状态转换表
# ──────────────────────────────────────────────

# 点击状态转换映射：当前状态 -> 目标状态
CLICK_TRANSITIONS: Dict[PuppyState, PuppyState] = {
    PuppyState.IDLE: PuppyState.WAGGING,
    PuppyState.WALKING: PuppyState.SITTING,
    PuppyState.SITTING: PuppyState.WAGGING,
    PuppyState.WAGGING: PuppyState.WAGGING,   # 连续点击保持开心
    PuppyState.YAWNING: PuppyState.IDLE,
    PuppyState.STRETCHING: PuppyState.WAGGING,
    PuppyState.SLEEPING: PuppyState.YAWNING,   # 睡觉时点击会醒来
    PuppyState.LYING_DOWN: PuppyState.IDLE,
}


# ──────────────────────────────────────────────
# 小黑狗事件处理器
# ──────────────────────────────────────────────

class PuppyEventHandlers:
    """小黑狗事件处理器集合

    管理所有与小黑狗交互相关的事件处理逻辑。
    处理器按优先级注册，确保拖拽过滤器最先执行。

    状态转换规则:
        - 单击: 根据当前状态触发不同互动动作
        - 双击: 触发趴下动作
        - 右键: 触发打哈欠动作
        - 拖拽: 移动窗口位置
    """

    def __init__(self, router: EventRouter, puppy, pet_window):
        """
        Args:
            router: 事件路由器
            puppy: 小黑狗实例
            pet_window: 宠物窗口实例

        Raises:
            TypeError: 参数类型错误
        """
        if router is None or puppy is None or pet_window is None:
            raise TypeError("router, puppy, pet_window 不能为 None")

        self.router = router
        self.puppy = puppy
        self.pet_window = pet_window

        # 拖拽状态
        self._drag_offset_x = 0
        self._drag_offset_y = 0

        # 悬停状态
        self._is_hovering = False

        # 注册所有处理器
        try:
            self._register_handlers()
            logger.info("小黑狗事件处理器初始化完成")
        except Exception as e:
            logger.error("小黑狗事件处理器初始化失败: %s", e, exc_info=True)
            raise

    def _register_handlers(self):
        """注册所有事件处理器

        优先级说明:
            - 拖拽过滤器: 优先级 0（最高，确保拖拽时不触发点击）
            - 拖拽事件: 优先级 10
            - 点击事件: 优先级 50
            - 悬停事件: 优先级 80
        """
        # 拖拽过滤器（最高优先级）
        self.router.add_filter(self._drag_filter)

        # 拖拽事件（高优先级）
        self.router.on(EventType.DRAG_START, self._on_drag_start, priority=10)
        self.router.on(EventType.DRAG_MOVE, self._on_drag_move, priority=10)
        self.router.on(EventType.DRAG_END, self._on_drag_end, priority=10)

        # 交互事件
        self.router.on(EventType.CLICK, self._on_click, priority=50)
        self.router.on(EventType.DOUBLE_CLICK, self._on_double_click, priority=50)
        self.router.on(EventType.RIGHT_CLICK, self._on_right_click, priority=50)

        # 悬停事件
        self.router.on(EventType.HOVER_ENTER, self._on_hover_enter, priority=80)
        self.router.on(EventType.HOVER_LEAVE, self._on_hover_leave, priority=80)

    # ──────────────────────────────────────────
    # 事件过滤器
    # ──────────────────────────────────────────

    def _drag_filter(self, event: Event) -> bool:
        """拖拽过滤器

        拖拽进行中时，阻止 CLICK 事件传播，避免拖拽结束时误触发点击。
        """
        if event.type == EventType.CLICK and self.router.is_dragging():
            logger.debug("拖拽进行中，阻止点击事件")
            return False
        return True

    # ──────────────────────────────────────────
    # 点击事件
    # ──────────────────────────────────────────

    def _on_click(self, event: Event):
        """处理点击事件

        根据当前状态触发不同的互动动作，使用状态转换表管理。
        """
        try:
            current_state = self.puppy.get_state()
            target_state = CLICK_TRANSITIONS.get(current_state)

            if target_state:
                self.puppy.set_state(target_state)
                logger.info("点击互动: %s -> %s", current_state.name, target_state.name)
            else:
                logger.debug("当前状态 %s 无点击转换规则", current_state.name)

            # 显示气泡消息
            message = self.puppy.get_state_message()
            self.pet_window.show_bubble(message)
        except Exception as e:
            logger.error("点击处理异常: %s", e, exc_info=True)

    # ──────────────────────────────────────────
    # 双击事件
    # ──────────────────────────────────────────

    def _on_double_click(self, event: Event):
        """处理双击事件

        双击触发趴下动作。
        """
        try:
            self.puppy.set_state(PuppyState.LYING_DOWN)
            message = self.puppy.get_state_message()
            self.pet_window.show_bubble(message)
            logger.info("双击: 趴下")
        except Exception as e:
            logger.error("双击处理异常: %s", e, exc_info=True)

    # ──────────────────────────────────────────
    # 右键事件
    # ──────────────────────────────────────────

    def _on_right_click(self, event: Event):
        """处理右键点击事件

        右键触发打哈欠动作。
        """
        try:
            self.puppy.set_state(PuppyState.YAWNING)
            message = self.puppy.get_state_message()
            self.pet_window.show_bubble(message)
            logger.info("右键: 打哈欠")
        except Exception as e:
            logger.error("右键处理异常: %s", e, exc_info=True)

    # ──────────────────────────────────────────
    # 拖拽事件
    # ──────────────────────────────────────────

    def _on_drag_start(self, event: Event):
        """处理拖拽开始

        记录鼠标按下位置相对于窗口左上角的偏移量。
        """
        window_pos = self.pet_window.get_position()
        self._drag_offset_x = event.x
        self._drag_offset_y = event.y

        # 拖拽时小黑狗回到空闲状态
        self.puppy.set_state(PuppyState.IDLE)
        logger.debug("开始拖拽 (窗口位置: %s)", window_pos)

    def _on_drag_move(self, event: Event):
        """处理拖拽移动

        根据鼠标当前位置和初始偏移量计算新窗口位置，实现平滑拖拽。
        """
        window_pos = self.pet_window.get_position()
        new_x = window_pos[0] + event.x - self._drag_offset_x
        new_y = window_pos[1] + event.y - self._drag_offset_y

        self.pet_window.set_position(new_x, new_y)

    def _on_drag_end(self, event: Event):
        """处理拖拽结束"""
        logger.debug("拖拽结束 (位置: %s)", self.pet_window.get_position())

    # ──────────────────────────────────────────
    # 悬停事件
    # ──────────────────────────────────────────

    def _on_hover_enter(self, event: Event):
        """处理鼠标进入"""
        self._is_hovering = True
        logger.debug("鼠标进入小黑狗区域")

    def _on_hover_leave(self, event: Event):
        """处理鼠标离开"""
        self._is_hovering = False
        logger.debug("鼠标离开小黑狗区域")

    # ──────────────────────────────────────────
    # 状态查询
    # ──────────────────────────────────────────

    def is_hovering(self) -> bool:
        """是否正在悬停"""
        return self._is_hovering


# ──────────────────────────────────────────────
# 窗口事件处理器
# ──────────────────────────────────────────────

class WindowEventHandlers:
    """窗口事件处理器集合

    管理窗口级别的事件处理，如关闭、最小化等。
    """

    def __init__(self, root: tk.Tk, pet_window):
        """
        Args:
            root: 主窗口
            pet_window: 宠物窗口实例
        """
        self.root = root
        self.pet_window = pet_window
        self._on_close_callback: Optional[Callable] = None
        self._setup_window_events()
        logger.info("窗口事件处理器初始化完成")

    def _setup_window_events(self):
        """设置窗口事件"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def on_close(self, callback: Callable) -> None:
        """注册关闭回调

        Args:
            callback: 关闭时调用的函数
        """
        self._on_close_callback = callback

    def _on_close(self):
        """处理窗口关闭"""
        logger.info("关闭应用")
        if self._on_close_callback:
            try:
                self._on_close_callback()
            except Exception as e:
                logger.error("关闭回调异常: %s", e)
        self.root.quit()
        self.root.destroy()


# ──────────────────────────────────────────────
# 键盘事件处理器
# ──────────────────────────────────────────────

class KeyboardEventHandlers:
    """键盘事件处理器集合

    管理键盘快捷键，如退出、暂停等。

    快捷键列表:
        q: 退出应用
        p: 暂停动画
        r: 恢复动画
        s: 坐下
        w: 走动
        空格: 互动
    """

    def __init__(self, router: EventRouter, app):
        """
        Args:
            router: 事件路由器
            app: 应用实例
        """
        self.router = router
        self.app = app

        # 快捷键映射
        self._key_bindings: Dict[str, Callable] = {
            'q': self._quit,
            'p': self._pause,
            'r': self._resume,
            's': self._sit,
            'w': self._walk,
            ' ': self._interact,
        }

        # 注册键盘处理器
        self.router.on(EventType.KEY_PRESS, self._on_key_press, priority=50)
        logger.info("键盘事件处理器初始化完成 (快捷键: %s)", list(self._key_bindings.keys()))

    def bind_key(self, key: str, handler: Callable) -> None:
        """绑定自定义快捷键

        Args:
            key: 按键字符
            handler: 处理函数
        """
        if not key or not callable(handler):
            logger.warning("无效的快捷键绑定: key=%s, handler=%s", key, handler)
            return
        self._key_bindings[key] = handler
        logger.debug("绑定快捷键: '%s'", key)

    def unbind_key(self, key: str) -> None:
        """解绑快捷键

        Args:
            key: 按键字符
        """
        if key in self._key_bindings:
            del self._key_bindings[key]
            logger.debug("解绑快捷键: '%s'", key)

    def _on_key_press(self, event: Event):
        """处理按键事件"""
        handler = self._key_bindings.get(event.key)
        if handler:
            logger.debug("触发快捷键: '%s'", event.key)
            try:
                handler()
            except Exception as e:
                logger.error("快捷键处理异常 [%s]: %s", event.key, e)

    def _quit(self):
        """退出应用"""
        logger.info("快捷键退出")
        self.app.stop()

    def _pause(self):
        """暂停动画"""
        logger.info("快捷键暂停")
        self.app.pause()

    def _resume(self):
        """恢复动画"""
        logger.info("快捷键恢复")
        self.app.resume()

    def _sit(self):
        """坐下"""
        from animations import PuppyState
        self.app.puppy.set_state(PuppyState.SITTING)
        logger.info("快捷键: 坐下")

    def _walk(self):
        """走动"""
        from animations import PuppyState
        self.app.puppy.set_state(PuppyState.WALKING)
        logger.info("快捷键: 走动")

    def _interact(self):
        """互动（模拟点击）"""
        self.app.puppy.on_click()
        logger.info("快捷键: 互动")


# ──────────────────────────────────────────────
# 上下文菜单处理器
# ──────────────────────────────────────────────

class ContextMenuHandler:
    """右键上下文菜单处理器

    提供精美的右键菜单功能，包含常用操作的快捷入口。
    v3 增强：更美观的暖色调样式、更多互动选项。
    """

    def __init__(self, router: EventRouter, pet_window, puppy, app):
        """
        Args:
            router: 事件路由器
            pet_window: 宠物窗口实例
            puppy: 小黑狗实例
            app: 应用实例
        """
        self.router = router
        self.pet_window = pet_window
        self.puppy = puppy
        self.app = app
        self._menu: Optional[tk.Menu] = None

        # 注册右键事件（低优先级，确保在其他处理器之后）
        self.router.on(EventType.RIGHT_CLICK, self._show_context_menu, priority=200)
        logger.info("上下文菜单处理器初始化完成")

    def _show_context_menu(self, event: Event):
        """显示上下文菜单"""
        try:
            # 创建菜单（暖色调样式）
            self._menu = tk.Menu(
                self.pet_window.get_window(),
                tearoff=0,
                bg="#fff8f0",
                fg="#5a3e28",
                activebackground="#e8c9a0",
                activeforeground="#3a2518",
                font=("微软雅黑", 9),
                relief=tk.SOLID,
                borderwidth=1,
            )

            # 互动动作
            self._menu.add_command(
                label="🐕 坐下",
                command=lambda: self._set_state(PuppyState.SITTING)
            )
            self._menu.add_command(
                label="🐾 趴下",
                command=lambda: self._set_state(PuppyState.LYING_DOWN)
            )
            self._menu.add_command(
                label="🚶 走动",
                command=lambda: self._set_state(PuppyState.WALKING)
            )
            self._menu.add_command(
                label="😴 打哈欠",
                command=lambda: self._set_state(PuppyState.YAWNING)
            )
            self._menu.add_command(
                label="💪 伸懒腰",
                command=lambda: self._set_state(PuppyState.STRETCHING)
            )
            self._menu.add_command(
                label="💤 睡觉",
                command=lambda: self._set_state(PuppyState.SLEEPING)
            )

            # 分隔线
            self._menu.add_separator()

            # 互动
            self._menu.add_command(
                label="✋ 摸摸头（摇尾巴）",
                command=lambda: self._set_state(PuppyState.WAGGING)
            )

            # 分隔线
            self._menu.add_separator()

            # 应用控制
            if self.app.running:
                self._menu.add_command(label="⏸ 暂停", command=self.app.pause)
            else:
                self._menu.add_command(label="▶ 继续", command=self.app.resume)

            # 分隔线
            self._menu.add_separator()

            # 退出
            self._menu.add_command(label="❌ 退出", command=self.app.stop)

            # 弹出菜单
            try:
                self._menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._menu.grab_release()

        except tk.TclError as e:
            logger.warning("显示上下文菜单 Tcl 错误: %s", e)
        except Exception as e:
            logger.error("显示上下文菜单异常: %s", e, exc_info=True)

    def _set_state(self, state: PuppyState):
        """设置小黑狗状态"""
        self.puppy.set_state(state)
        message = self.puppy.get_state_message()
        self.pet_window.show_bubble(message)
        logger.info("上下文菜单: 切换到 %s", state.name)
