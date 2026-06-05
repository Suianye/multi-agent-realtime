"""
程序入口测试
"""
import pytest
import tkinter as tk
from main import PuppyDesktopPet


def test_app_initialization():
    """测试应用初始化"""
    app = PuppyDesktopPet()
    assert app.root is not None
    assert app.pet_window is not None
    assert app.puppy is not None
    app.root.destroy()


def test_app_start_stop():
    """测试应用启动停止"""
    app = PuppyDesktopPet()
    # 启动后立即停止（避免阻塞）
    app.root.after(100, app.stop)
    app.start()
    # 验证应用已停止
    assert not app.running


def test_app_click_handler():
    """测试点击处理"""
    app = PuppyDesktopPet()
    # 模拟点击事件
    event = type('Event', (), {'x': 50, 'y': 60})()
    app._on_canvas_click(event)
    # 验证状态可能改变
    app.root.destroy()
