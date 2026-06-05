"""
小黑狗桌宠程序入口
"""
import tkinter as tk
from pet_window import PetWindow
from puppy import Puppy
from config import WINDOW_TITLE


class PuppyDesktopPet:
    """小黑狗桌宠应用"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.withdraw()  # 隐藏主窗口

        # 创建宠物窗口
        self.pet_window = PetWindow(self.root)
        self.canvas = self.pet_window.get_canvas()

        # 创建小黑狗
        self.puppy = Puppy(self.canvas)

        # 绑定点击事件
        self.canvas.bind('<Button-1>', self._on_canvas_click)

        # 运行状态
        self.running = False

        # 设置初始位置（屏幕右下角）
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.pet_window.set_position(screen_width - 150, screen_height - 200)

    def _on_canvas_click(self, event):
        """处理 Canvas 点击事件"""
        self.puppy.on_click()

    def _update(self):
        """更新循环"""
        if self.running:
            self.puppy.update()
            self.root.after(100, self._update)

    def start(self):
        """启动应用"""
        self.running = True
        self._update()
        self.root.mainloop()

    def stop(self):
        """停止应用"""
        self.running = False
        self.root.quit()


def main():
    """主函数"""
    app = PuppyDesktopPet()
    app.start()


if __name__ == "__main__":
    main()
