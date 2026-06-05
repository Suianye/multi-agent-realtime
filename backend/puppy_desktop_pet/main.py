"""
小黑狗桌宠程序入口
使用事件路由系统处理所有用户交互

功能:
    1. 初始化所有模块（窗口、小黑狗、事件路由、处理器）
    2. 管理应用生命周期（启动、暂停、恢复、停止）
    3. 运行主循环，驱动状态更新和动画渲染
    4. 完整的错误处理和优雅退出
"""
import sys
import signal
import tkinter as tk
from typing import Optional

from pet_window import PetWindow
from puppy import Puppy
from event_router import EventRouter
from handlers import (
    PuppyEventHandlers,
    WindowEventHandlers,
    KeyboardEventHandlers,
    ContextMenuHandler,
)
from config import WINDOW_TITLE, validate_all_configs, get_config_summary
from logger import setup_logging, get_logger, log_exception

# 初始化日志系统
setup_logging(level="INFO", log_to_file=True, debug_mode=False)
logger = get_logger("main")


class PuppyDesktopPet:
    """小黑狗桌宠应用

    主应用类，负责：
    1. 初始化所有模块
    2. 设置事件路由系统
    3. 管理应用生命周期

    包含完整的错误处理和优雅退出机制。
    """

    def __init__(self):
        """初始化应用

        Raises:
            RuntimeError: 初始化失败时抛出
        """
        self.root: Optional[tk.Tk] = None
        self.pet_window: Optional[PetWindow] = None
        self.canvas: Optional[tk.Canvas] = None
        self.puppy: Optional[Puppy] = None
        self.event_router: Optional[EventRouter] = None
        self.puppy_handlers: Optional[PuppyEventHandlers] = None
        self.window_handlers: Optional[WindowEventHandlers] = None
        self.keyboard_handlers: Optional[KeyboardEventHandlers] = None
        self.context_menu_handler: Optional[ContextMenuHandler] = None

        # 运行状态
        self.running = False
        self._initialized = False
        self._shutting_down = False

        # 气泡消息计数器
        self._bubble_counter = 0
        self._bubble_interval = 30  # 每 3 秒检查一次（100ms * 30）

        # 记录上一次的状态
        self._last_state = None

        # 更新定时器 ID
        self._update_timer_id: Optional[str] = None

        try:
            logger.info("正在初始化小黑狗桌宠...")

            # 验证配置
            self._validate_config()

            # 创建主窗口
            self.root = tk.Tk()
            self.root.title(WINDOW_TITLE)
            self.root.withdraw()  # 隐藏主窗口

            # 注册信号处理（优雅退出）
            self._setup_signal_handlers()

            # 创建宠物窗口
            self.pet_window = PetWindow(self.root)
            self.canvas = self.pet_window.get_canvas()

            # 创建小黑狗
            self.puppy = Puppy(self.canvas)

            # 记录初始状态
            self._last_state = self.puppy.get_state()

            # 创建事件路由器
            self.event_router = EventRouter(self.canvas)

            # 创建事件处理器
            self.puppy_handlers = PuppyEventHandlers(
                self.event_router, self.puppy, self.pet_window
            )
            self.window_handlers = WindowEventHandlers(self.root, self.pet_window)
            self.keyboard_handlers = KeyboardEventHandlers(self.event_router, self)
            self.context_menu_handler = ContextMenuHandler(
                self.event_router, self.pet_window, self.puppy, self
            )

            # 注册关闭回调
            self.window_handlers.on_close(self._on_app_close)

            # 设置初始位置（屏幕右下角）
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.pet_window.set_position(screen_width - 150, screen_height - 200)

            # 启用 Canvas 键盘焦点
            self.canvas.focus_set()

            # 显示欢迎消息
            self.pet_window.show_bubble("汪~ 我是小黑狗！", 3000)

            self._initialized = True

            logger.info("小黑狗桌宠初始化完成")
            print("小黑狗桌宠已初始化")
            print("操作说明:")
            print("  - 单击: 互动（摇尾巴/坐下）")
            print("  - 双击: 趴下")
            print("  - 右键: 上下文菜单")
            print("  - 拖拽: 移动位置")
            print("  - 键盘: q=退出, p=暂停, r=恢复, s=坐下, w=走动, 空格=互动")

        except Exception as e:
            log_exception(logger, "初始化小黑狗桌宠失败", e)
            self._emergency_cleanup()
            raise RuntimeError(f"无法初始化小黑狗桌宠: {e}") from e

    def _validate_config(self) -> None:
        """验证配置参数"""
        errors = validate_all_configs(strict=False)
        if errors:
            for name, error in errors.items():
                logger.warning(f"配置验证: {error}")
        else:
            logger.debug("配置验证通过")

        summary = get_config_summary()
        logger.debug(f"配置摘要: {summary}")

    def _setup_signal_handlers(self) -> None:
        """设置信号处理器（用于优雅退出）"""
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            logger.debug("已注册 SIGINT 信号处理器")
        except (OSError, AttributeError):
            logger.debug("无法注册信号处理器（Windows 限制）")

    def _signal_handler(self, signum, frame) -> None:
        """信号处理器

        Args:
            signum: 信号编号
            frame: 当前栈帧
        """
        logger.info(f"收到信号 {signum}，准备退出...")
        self.stop()

    def _on_app_close(self) -> None:
        """应用关闭回调"""
        logger.info("应用关闭回调触发")
        self._cleanup()

    def _update(self):
        """更新循环

        分离状态更新和动画更新：
        - 状态更新: 每 100ms 一次
        - 气泡消息: 每 3 秒检查一次状态变化
        """
        if not self.running or self._shutting_down:
            return

        try:
            # 更新小黑狗状态
            if self.puppy:
                self.puppy.update()

            # 检查状态变化并显示气泡
            self._bubble_counter += 1
            if self._bubble_counter >= self._bubble_interval:
                self._bubble_counter = 0
                if self.puppy and self.pet_window:
                    current_state = self.puppy.get_state()
                    if current_state != self._last_state:
                        old_name = self._last_state.name if self._last_state else "N/A"
                        self._last_state = current_state
                        message = self.puppy.get_state_message()
                        self.pet_window.show_bubble(message)
                        logger.debug("状态变化气泡: %s -> %s", old_name, current_state.name)

            # 调度下一次更新
            if self.root and self.running:
                self._update_timer_id = self.root.after(100, self._update)

        except tk.TclError as e:
            logger.debug(f"更新循环 Tcl 错误（窗口可能已关闭）: {e}")
            self.running = False
        except Exception as e:
            log_exception(logger, "更新循环异常", e)
            # 不停止循环，尝试继续
            if self.root and self.running:
                try:
                    self._update_timer_id = self.root.after(100, self._update)
                except tk.TclError:
                    self.running = False

    def start(self):
        """启动应用

        Raises:
            RuntimeError: 应用未初始化时抛出
        """
        if not self._initialized:
            raise RuntimeError("应用未初始化，无法启动")

        try:
            self.running = True
            self._update()
            logger.info("小黑狗桌宠已启动")
            print("小黑狗桌宠已启动！")

            # 启动主循环
            self.root.mainloop()

        except KeyboardInterrupt:
            logger.info("程序被用户中断 (Ctrl+C)")
            print("\n程序被用户中断")
            self.stop()
        except Exception as e:
            log_exception(logger, "主循环异常", e)
            self.stop()
            raise

    def stop(self):
        """停止应用"""
        if self._shutting_down:
            return

        self._shutting_down = True
        logger.info("正在停止小黑狗桌宠...")

        try:
            self._cleanup()

            if self.root:
                try:
                    self.root.quit()
                except tk.TclError:
                    pass

                try:
                    self.root.destroy()
                except tk.TclError:
                    pass

            logger.info("小黑狗桌宠已停止")
            print("小黑狗桌宠已停止")

        except Exception as e:
            log_exception(logger, "停止应用异常", e)
        finally:
            self.running = False
            self._shutting_down = False

    def _cleanup(self) -> None:
        """清理资源"""
        self.running = False

        # 取消更新定时器
        if self._update_timer_id and self.root:
            try:
                self.root.after_cancel(self._update_timer_id)
            except (ValueError, tk.TclError):
                pass
            self._update_timer_id = None

        # 清理事件路由器
        if self.event_router:
            try:
                self.event_router.destroy()
            except Exception as e:
                logger.debug(f"清理事件路由器异常: {e}")

        # 清理宠物窗口
        if self.pet_window:
            try:
                self.pet_window.destroy()
            except Exception as e:
                logger.debug(f"清理宠物窗口异常: {e}")

        logger.debug("资源清理完成")

    def _emergency_cleanup(self) -> None:
        """紧急清理（初始化失败时调用）"""
        logger.warning("执行紧急清理")

        try:
            if self.pet_window:
                try:
                    self.pet_window.destroy()
                except Exception:
                    pass

            if self.root:
                try:
                    self.root.quit()
                    self.root.destroy()
                except Exception:
                    pass
        except Exception:
            pass

    def pause(self):
        """暂停动画"""
        if not self._initialized:
            return

        self.running = False
        if self.pet_window:
            try:
                self.pet_window.show_bubble("暂停了~", 1500)
            except Exception:
                pass
        logger.info("已暂停")
        print("已暂停")

    def resume(self):
        """恢复动画"""
        if not self._initialized:
            return

        if not self.running:
            self.running = True
            self._update()
            if self.pet_window:
                try:
                    self.pet_window.show_bubble("继续玩~", 1500)
                except Exception:
                    pass
            logger.info("已恢复")
            print("已恢复")

    def get_state(self) -> dict:
        """获取应用状态（用于调试）

        Returns:
            包含应用状态信息的字典
        """
        try:
            return {
                "running": self.running,
                "initialized": self._initialized,
                "shutting_down": self._shutting_down,
                "puppy_state": self.puppy.get_state().name if self.puppy else "N/A",
                "puppy_position": self.puppy.get_position() if self.puppy else (0, 0),
                "window_position": self.pet_window.get_position() if self.pet_window else (0, 0),
                "is_dragging": self.event_router.is_dragging() if self.event_router else False,
                "event_stats": self.event_router.get_event_stats() if self.event_router else {},
            }
        except Exception as e:
            log_exception(logger, "获取应用状态异常", e)
            return {"error": str(e)}


def main() -> int:
    """主函数

    Returns:
        退出码 (0=正常, 1=错误)
    """
    app = None

    try:
        logger.info("=" * 50)
        logger.info("小黑狗桌宠启动")
        logger.info("=" * 50)

        app = PuppyDesktopPet()
        app.start()

        logger.info("小黑狗桌宠正常退出")
        return 0

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        print("\n程序被用户中断")
        return 0

    except RuntimeError as e:
        logger.error(f"运行时错误: {e}")
        print(f"程序错误: {e}")
        return 1

    except Exception as e:
        log_exception(logger, "未预期的错误", e)
        print(f"程序错误: {e}")
        return 1

    finally:
        # 确保资源被清理
        if app is not None:
            try:
                app.stop()
            except Exception:
                pass

        logger.info("=" * 50)
        logger.info("小黑狗桌宠结束")
        logger.info("=" * 50)


if __name__ == "__main__":
    sys.exit(main())
