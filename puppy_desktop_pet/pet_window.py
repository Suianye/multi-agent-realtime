"""
窗口管理模块
管理透明窗口和拖拽移动
"""
import tkinter as tk
from config import CANVAS_WIDTH, CANVAS_HEIGHT, WINDOW_TITLE


class PetWindow:
    """宠物窗口管理器"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.title(WINDOW_TITLE)
        self.window.overrideredirect(True)  # 去掉标题栏
        self.window.attributes('-topmost', True)  # 始终在最前

        # 设置透明背景（Windows）
        try:
            self.window.attributes('-transparentcolor', 'white')
        except:
            pass  # macOS/Linux 可能不支持

        # 创建 Canvas
        self.canvas = tk.Canvas(
            self.window,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg='white',
            highlightthickness=0
        )
        self.canvas.pack()

        # 拖拽状态
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.x = 0
        self.y = 0

        # 绑定拖拽事件
        self.canvas.bind('<Button-1>', self._on_drag_start)
        self.canvas.bind('<B1-Motion>', self._on_drag_move)
        self.canvas.bind('<ButtonRelease-1>', self._on_drag_end)

    def _on_drag_start(self, event):
        """拖拽开始"""
        self.dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def _on_drag_move(self, event):
        """拖拽移动"""
        if self.dragging:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            self.x += dx
            self.y += dy
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            self.window.geometry(f'+{self.x}+{self.y}')

    def _on_drag_end(self, event):
        """拖拽结束"""
        self.dragging = False

    def set_position(self, x: int, y: int):
        """设置窗口位置"""
        self.x = x
        self.y = y
        self.window.geometry(f'+{x}+{y}')

    def get_position(self) -> tuple:
        """获取窗口位置"""
        return (self.x, self.y)

    def get_canvas(self) -> tk.Canvas:
        """获取 Canvas"""
        return self.canvas

    def update(self):
        """更新窗口"""
        self.window.update()
