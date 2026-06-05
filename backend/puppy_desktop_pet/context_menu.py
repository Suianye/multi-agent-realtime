"""
右键菜单模块
为小黑狗桌宠提供右键弹出菜单功能
支持各种互动动作和应用控制
"""
import tkinter as tk
from typing import Callable, Optional, Dict
from animations import PuppyState
from logger import get_logger

logger = get_logger("context_menu")


class ContextMenu:
    """右键菜单管理器

    提供精美的右键弹出菜单，包含：
    - 互动动作（坐下、趴下、走动、打哈欠等）
    - 应用控制（暂停、退出）
    - 状态显示
    """

    def __init__(self, root: tk.Tk, canvas: tk.Canvas):
        """初始化右键菜单

        Args:
            root: tkinter 根窗口
            canvas: 绑定右键事件的 Canvas
        """
        self.root = root
        self.canvas = canvas
        self.menu: Optional[tk.Menu] = None
        self._callbacks: Dict[str, Callable] = {}

        # 绑定右键事件
        self.canvas.bind('<Button-3>', self._show_menu)

        logger.debug("右键菜单已初始化")

    def set_callback(self, action: str, callback: Callable) -> None:
        """设置动作回调

        Args:
            action: 动作名称
            callback: 回调函数
        """
        self._callbacks[action] = callback

    def _show_menu(self, event) -> None:
        """显示右键菜单

        Args:
            event: tkinter 事件
        """
        # 销毁旧菜单
        if self.menu:
            try:
                self.menu.destroy()
            except Exception:
                pass

        # 创建新菜单
        self.menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#fff8f0",
            fg="#5a3e28",
            activebackground="#e8c9a0",
            activeforeground="#3a2518",
            font=("微软雅黑", 9),
            relief=tk.SOLID,
            borderwidth=1,
        )

        # 添加互动动作
        self.menu.add_command(
            label="🐕 坐下",
            command=lambda: self._on_action("sit")
        )
        self.menu.add_command(
            label="🐾 趴下",
            command=lambda: self._on_action("lie_down")
        )
        self.menu.add_command(
            label="🚶 走动",
            command=lambda: self._on_action("walk")
        )
        self.menu.add_command(
            label="😴 打哈欠",
            command=lambda: self._on_action("yawn")
        )
        self.menu.add_command(
            label="💪 伸懒腰",
            command=lambda: self._on_action("stretch")
        )
        self.menu.add_command(
            label="💤 睡觉",
            command=lambda: self._on_action("sleep")
        )

        # 分隔线
        self.menu.add_separator()

        # 互动
        self.menu.add_command(
            label="✋ 摸摸头",
            command=lambda: self._on_action("pet")
        )
        self.menu.add_command(
            label="🍖 喂食",
            command=lambda: self._on_action("feed")
        )

        # 分隔线
        self.menu.add_separator()

        # 应用控制
        self.menu.add_command(
            label="⏸ 暂停/继续",
            command=lambda: self._on_action("toggle_pause")
        )

        # 分隔线
        self.menu.add_separator()

        # 退出
        self.menu.add_command(
            label="❌ 退出",
            command=lambda: self._on_action("quit")
        )

        # 显示菜单
        try:
            self.menu.post(event.x_root, event.y_root)
        except Exception as e:
            logger.warning(f"显示菜单失败: {e}")

    def _on_action(self, action: str) -> None:
        """处理菜单动作

        Args:
            action: 动作名称
        """
        callback = self._callbacks.get(action)
        if callback:
            try:
                callback()
                logger.debug(f"菜单动作: {action}")
            except Exception as e:
                logger.warning(f"执行菜单动作 '{action}' 失败: {e}")
        else:
            logger.debug(f"未注册的菜单动作: {action}")

    def destroy(self) -> None:
        """销毁菜单"""
        if self.menu:
            try:
                self.menu.destroy()
            except Exception:
                pass
            self.menu = None
