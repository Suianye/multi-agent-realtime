"""
小黑狗桌宠 v3

一个可爱的桌面宠物应用，使用 Python + tkinter 实现。

模块说明:
    - config: 全局配置常量
    - logger: 日志系统
    - animations: 动画帧管理与状态定义
    - puppy_drawer: Canvas 绘制模块
    - puppy: 小黑狗核心逻辑与状态机
    - pet_window: 窗口管理（透明窗口、拖拽、气泡）
    - event_router: 事件路由系统
    - handlers: 事件处理器集合
    - main: 应用入口
"""

from animations import PuppyState, AnimationManager
from puppy import Puppy
from pet_window import PetWindow
from event_router import EventRouter, EventType, Event
from handlers import PuppyEventHandlers, WindowEventHandlers, KeyboardEventHandlers

__version__ = "3.0.0"
__all__ = [
    "PuppyState",
    "AnimationManager",
    "Puppy",
    "PetWindow",
    "EventRouter",
    "EventType",
    "Event",
    "PuppyEventHandlers",
    "WindowEventHandlers",
    "KeyboardEventHandlers",
]
