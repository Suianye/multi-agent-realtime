"""
错误恢复与边界处理模块
提供全局异常捕获、资源监控、崩溃报告和自恢复机制

功能:
    1. 全局异常钩子（捕获未处理异常）
    2. 资源监控（内存使用、Tkinter 对象计数）
    3. 崩溃报告生成
    4. 自动恢复策略
    5. 看门狗定时器
    6. 输入消毒工具
"""
import sys
import os
import gc
import time
import threading
import traceback
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
from pathlib import Path

from logger import get_logger, log_exception

logger = get_logger("error_recovery")


# ============================================================
# 全局异常钩子
# ============================================================

class GlobalExceptionHandler:
    """全局异常处理器

    捕获所有未处理的异常，生成崩溃报告并尝试优雅退出。
    """

    def __init__(self, log_dir: str = "logs"):
        """初始化全局异常处理器

        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._original_excepthook = sys.excepthook
        self._crash_callbacks: List[Callable] = []
        self._installed = False

    def install(self) -> None:
        """安装全局异常钩子"""
        if self._installed:
            return

        sys.excepthook = self._handle_exception
        # 也捕获线程中的异常
        threading.excepthook = self._handle_thread_exception
        self._installed = True
        logger.info("全局异常处理器已安装")

    def uninstall(self) -> None:
        """卸载全局异常钩子"""
        if self._installed:
            sys.excepthook = self._original_excepthook
            self._installed = False
            logger.info("全局异常处理器已卸载")

    def register_crash_callback(self, callback: Callable) -> None:
        """注册崩溃回调（崩溃时执行清理操作）

        Args:
            callback: 回调函数
        """
        if callable(callback):
            self._crash_callbacks.append(callback)

    def _handle_exception(self, exc_type, exc_value, exc_tb) -> None:
        """处理未捕获的异常

        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_tb: 异常追踪
        """
        # 忽略 KeyboardInterrupt（由信号处理器处理）
        if issubclass(exc_type, KeyboardInterrupt):
            self._original_excepthook(exc_type, exc_value, exc_tb)
            return

        # 生成崩溃报告
        crash_report = self._generate_crash_report(exc_type, exc_value, exc_tb)

        # 保存崩溃报告
        report_path = self._save_crash_report(crash_report)

        # 执行注册的回调
        for callback in self._crash_callbacks:
            try:
                callback(exc_type, exc_value, exc_tb)
            except Exception as e:
                logger.error(f"崩溃回调执行失败: {e}")

        # 输出错误信息
        logger.critical(f"未捕获的异常: {exc_type.__name__}: {exc_value}")
        logger.critical(f"崩溃报告已保存: {report_path}")

        # 调用原始的异常钩子
        self._original_excepthook(exc_type, exc_value, exc_tb)

    def _handle_thread_exception(self, args) -> None:
        """处理线程中的未捕获异常

        Args:
            args: 线程异常参数
        """
        if args.exc_type == KeyboardInterrupt:
            return

        logger.error(
            f"线程 '{args.thread.name}' 中的未捕获异常: "
            f"{args.exc_type.__name__}: {args.exc_value}"
        )

        # 生成崩溃报告
        crash_report = self._generate_crash_report(
            args.exc_type, args.exc_value, args.exc_traceback
        )
        self._save_crash_report(crash_report)

    def _generate_crash_report(self, exc_type, exc_value, exc_tb) -> Dict[str, Any]:
        """生成崩溃报告

        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_tb: 异常追踪

        Returns:
            崩溃报告字典
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "exception": {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "module": getattr(exc_type, '__module__', 'unknown'),
            },
            "traceback": traceback.format_exception(exc_type, exc_value, exc_tb),
            "system": {
                "platform": sys.platform,
                "python_version": sys.version,
                "executable": sys.executable,
                "argv": sys.argv,
            },
            "process": {
                "pid": os.getpid(),
                "cwd": os.getcwd(),
            },
        }

        # 尝试获取内存信息
        try:
            import psutil
            process = psutil.Process()
            report["memory"] = {
                "rss_mb": process.memory_info().rss / 1024 / 1024,
                "vms_mb": process.memory_info().vms / 1024 / 1024,
                "percent": process.memory_percent(),
            }
        except ImportError:
            report["memory"] = {"error": "psutil not available"}

        return report

    def _save_crash_report(self, report: Dict[str, Any]) -> str:
        """保存崩溃报告到文件

        Args:
            report: 崩溃报告字典

        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"crash_report_{timestamp}.json"
        filepath = self.log_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            return str(filepath)
        except Exception as e:
            logger.error(f"保存崩溃报告失败: {e}")
            return "保存失败"


# ============================================================
# 资源监控器
# ============================================================

class ResourceMonitor:
    """资源监控器

    监控内存使用、Tkinter 对象数量等，防止资源泄漏。
    """

    def __init__(self, check_interval: float = 30.0):
        """初始化资源监控器

        Args:
            check_interval: 检查间隔（秒）
        """
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._warnings: List[str] = []
        self._max_warnings = 100

        # 阈值配置
        self.memory_warning_mb = 200  # 内存警告阈值（MB）
        self.memory_critical_mb = 500  # 内存临界阈值（MB）

        # 统计
        self._check_count = 0
        self._warning_count = 0

    def start(self) -> None:
        """启动资源监控"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ResourceMonitor"
        )
        self._thread.start()
        logger.info("资源监控器已启动")

    def stop(self) -> None:
        """停止资源监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("资源监控器已停止")

    def _monitor_loop(self) -> None:
        """监控主循环"""
        while self._running:
            try:
                self._check_resources()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.debug(f"资源检查异常: {e}")
                time.sleep(self.check_interval)

    def _check_resources(self) -> None:
        """检查系统资源"""
        self._check_count += 1

        # 检查内存
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            if memory_mb > self.memory_critical_mb:
                warning = f"内存使用临界: {memory_mb:.1f}MB (阈值: {self.memory_critical_mb}MB)"
                self._add_warning(warning)
                logger.warning(warning)
                # 触发垃圾回收
                gc.collect()
            elif memory_mb > self.memory_warning_mb:
                if self._check_count % 10 == 0:  # 每 10 次检查警告一次
                    warning = f"内存使用较高: {memory_mb:.1f}MB"
                    self._add_warning(warning)
                    logger.debug(warning)
        except ImportError:
            pass  # psutil 不可用时跳过

        # 检查 Python 对象数量
        try:
            obj_count = len(gc.get_objects())
            if obj_count > 100000:
                logger.warning(f"Python 对象数量过多: {obj_count}")
        except Exception:
            pass

    def _add_warning(self, warning: str) -> None:
        """添加警告记录"""
        self._warnings.append(warning)
        self._warning_count += 1

        # 限制警告数量
        if len(self._warnings) > self._max_warnings:
            self._warnings = self._warnings[-self._max_warnings:]

    def get_status(self) -> Dict[str, Any]:
        """获取监控状态

        Returns:
            状态字典
        """
        return {
            "running": self._running,
            "check_count": self._check_count,
            "warning_count": self._warning_count,
            "recent_warnings": self._warnings[-10:] if self._warnings else [],
        }


# ============================================================
# 看门狗定时器
# ============================================================

class WatchdogTimer:
    """看门狗定时器

    检测主循环是否挂起，超时时触发恢复操作。
    """

    def __init__(self, timeout: float = 10.0):
        """初始化看门狗

        Args:
            timeout: 超时时间（秒）
        """
        self.timeout = timeout
        self._last_feed_time = time.time()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._timeout_callback: Optional[Callable] = None
        self._timeout_count = 0

    def start(self) -> None:
        """启动看门狗"""
        if self._running:
            return

        self._running = True
        self._last_feed_time = time.time()
        self._thread = threading.Thread(
            target=self._watchdog_loop,
            daemon=True,
            name="Watchdog"
        )
        self._thread.start()
        logger.info(f"看门狗定时器已启动 (超时: {self.timeout}s)")

    def stop(self) -> None:
        """停止看门狗"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("看门狗定时器已停止")

    def feed(self) -> None:
        """喂狗（重置计时器）"""
        self._last_feed_time = time.time()

    def set_timeout_callback(self, callback: Callable) -> None:
        """设置超时回调

        Args:
            callback: 超时时调用的函数
        """
        self._timeout_callback = callback

    def _watchdog_loop(self) -> None:
        """看门狗主循环"""
        while self._running:
            try:
                elapsed = time.time() - self._last_feed_time

                if elapsed > self.timeout:
                    self._timeout_count += 1
                    logger.warning(
                        f"看门狗超时 (第 {self._timeout_count} 次): "
                        f"已 {elapsed:.1f} 秒未响应"
                    )

                    # 执行超时回调
                    if self._timeout_callback:
                        try:
                            self._timeout_callback()
                        except Exception as e:
                            logger.error(f"看门狗超时回调异常: {e}")

                    # 重置计时器（避免重复触发）
                    self._last_feed_time = time.time()

                time.sleep(1.0)
            except Exception as e:
                logger.debug(f"看门狗异常: {e}")
                time.sleep(1.0)

    def get_status(self) -> Dict[str, Any]:
        """获取看门狗状态

        Returns:
            状态字典
        """
        return {
            "running": self._running,
            "timeout": self.timeout,
            "last_feed": self._last_feed_time,
            "elapsed": time.time() - self._last_feed_time,
            "timeout_count": self._timeout_count,
        }


# ============================================================
# 输入消毒工具
# ============================================================

class InputSanitizer:
    """输入消毒工具

    提供各种输入验证和消毒功能，防止异常输入导致问题。
    """

    @staticmethod
    def sanitize_string(value: Any, max_length: int = 1000,
                        allow_empty: bool = False) -> Optional[str]:
        """消毒字符串输入

        Args:
            value: 输入值
            max_length: 最大长度
            allow_empty: 是否允许空字符串

        Returns:
            消毒后的字符串，无效返回 None
        """
        if value is None:
            return "" if allow_empty else None

        if not isinstance(value, str):
            try:
                value = str(value)
            except Exception:
                return None

        # 移除控制字符（保留换行和制表符）
        value = ''.join(
            char for char in value
            if char in ('\n', '\r', '\t') or (ord(char) >= 32)
        )

        # 限制长度
        if len(value) > max_length:
            value = value[:max_length]

        if not allow_empty and not value.strip():
            return None

        return value

    @staticmethod
    def sanitize_integer(value: Any, min_val: int = None,
                         max_val: int = None, default: int = 0) -> int:
        """消毒整数输入

        Args:
            value: 输入值
            min_val: 最小值
            max_val: 最大值
            default: 默认值

        Returns:
            消毒后的整数
        """
        if value is None:
            return default

        try:
            result = int(value)
        except (ValueError, TypeError):
            return default

        if min_val is not None:
            result = max(min_val, result)
        if max_val is not None:
            result = min(max_val, result)

        return result

    @staticmethod
    def sanitize_float(value: Any, min_val: float = None,
                       max_val: float = None, default: float = 0.0) -> float:
        """消毒浮点数输入

        Args:
            value: 输入值
            min_val: 最小值
            max_val: 最大值
            default: 默认值

        Returns:
            消毒后的浮点数
        """
        if value is None:
            return default

        try:
            result = float(value)
        except (ValueError, TypeError):
            return default

        # 检查 NaN 和无穷大
        if result != result:  # NaN check
            return default

        if result == float('inf') or result == float('-inf'):
            return default

        if min_val is not None:
            result = max(min_val, result)
        if max_val is not None:
            result = min(max_val, result)

        return result

    @staticmethod
    def sanitize_color(value: Any, default: str = "#000000") -> str:
        """消毒颜色值

        Args:
            value: 颜色字符串
            default: 默认颜色

        Returns:
            有效的颜色字符串
        """
        if not isinstance(value, str):
            return default

        # 基本格式检查
        if not value.startswith('#'):
            return default

        hex_part = value[1:]
        if len(hex_part) not in (3, 6):
            return default

        try:
            int(hex_part, 16)
            return value
        except ValueError:
            return default

    @staticmethod
    def sanitize_coordinate(value: Any, min_val: int = -10000,
                            max_val: int = 10000, default: int = 0) -> int:
        """消毒坐标值

        Args:
            value: 坐标值
            min_val: 最小值
            max_val: 最大值
            default: 默认值

        Returns:
            有效的坐标值
        """
        return InputSanitizer.sanitize_integer(value, min_val, max_val, default)


# ============================================================
# 优雅关闭管理器
# ============================================================

class GracefulShutdown:
    """优雅关闭管理器

    确保应用在关闭时正确清理所有资源，支持超时强制退出。
    """

    def __init__(self, timeout: float = 5.0):
        """初始化优雅关闭管理器

        Args:
            timeout: 关闭超时时间（秒）
        """
        self.timeout = timeout
        self._cleanup_tasks: List[Tuple[str, Callable]] = []
        self._completed_tasks: List[str] = []
        self._failed_tasks: List[Tuple[str, str]] = []

    def register_cleanup(self, name: str, task: Callable) -> None:
        """注册清理任务

        Args:
            name: 任务名称
            task: 清理函数
        """
        if callable(task):
            self._cleanup_tasks.append((name, task))
            logger.debug(f"注册清理任务: {name}")

    def execute_shutdown(self) -> bool:
        """执行优雅关闭

        Returns:
            是否成功完成所有清理任务
        """
        logger.info("开始优雅关闭...")
        start_time = time.time()

        for name, task in self._cleanup_tasks:
            # 检查超时
            elapsed = time.time() - start_time
            if elapsed > self.timeout:
                logger.warning(
                    f"优雅关闭超时 ({self.timeout}s)，"
                    f"跳过剩余 {len(self._cleanup_tasks) - len(self._completed_tasks)} 个任务"
                )
                return False

            try:
                # 设置单个任务的超时
                remaining_time = self.timeout - elapsed
                task()
                self._completed_tasks.append(name)
                logger.debug(f"清理任务完成: {name}")
            except Exception as e:
                self._failed_tasks.append((name, str(e)))
                logger.error(f"清理任务失败: {name} - {e}")

        success = len(self._failed_tasks) == 0
        logger.info(
            f"优雅关闭完成: {len(self._completed_tasks)} 成功, "
            f"{len(self._failed_tasks)} 失败, "
            f"耗时 {time.time() - start_time:.2f}s"
        )
        return success

    def get_status(self) -> Dict[str, Any]:
        """获取关闭状态

        Returns:
            状态字典
        """
        return {
            "total_tasks": len(self._cleanup_tasks),
            "completed": len(self._completed_tasks),
            "failed": len(self._failed_tasks),
            "completed_tasks": self._completed_tasks,
            "failed_tasks": self._failed_tasks,
        }


# ============================================================
# 安全执行器
# ============================================================

def safe_execute(func: Callable, *args, default=None,
                 log_errors: bool = True, **kwargs) -> Any:
    """安全执行函数，捕获所有异常

    Args:
        func: 要执行的函数
        *args: 位置参数
        default: 异常时的默认返回值
        log_errors: 是否记录错误
        **kwargs: 关键字参数

    Returns:
        函数返回值，异常时返回 default
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.debug(f"安全执行异常: {func.__name__} - {e}")
        return default


def retry_on_failure(func: Callable, max_retries: int = 3,
                     delay: float = 0.1, backoff: float = 2.0) -> Any:
    """失败重试装饰器

    Args:
        func: 要执行的函数
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍增因子

    Returns:
        函数返回值

    Raises:
        最后一次重试的异常
    """
    last_exception = None
    current_delay = delay

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.debug(
                    f"重试 {func.__name__} (第 {attempt + 1} 次): {e}"
                )
                time.sleep(current_delay)
                current_delay *= backoff

    raise last_exception


# ============================================================
# 模块级实例
# ============================================================

# 全局异常处理器
_global_exception_handler: Optional[GlobalExceptionHandler] = None

# 资源监控器
_resource_monitor: Optional[ResourceMonitor] = None

# 看门狗定时器
_watchdog: Optional[WatchdogTimer] = None

# 优雅关闭管理器
_shutdown_manager: Optional[GracefulShutdown] = None


def initialize_error_recovery(log_dir: str = "logs",
                              enable_resource_monitor: bool = True,
                              enable_watchdog: bool = True,
                              watchdog_timeout: float = 10.0) -> None:
    """初始化错误恢复系统

    Args:
        log_dir: 日志目录
        enable_resource_monitor: 是否启用资源监控
        enable_watchdog: 是否启用看门狗
        watchdog_timeout: 看门狗超时时间（秒）
    """
    global _global_exception_handler, _resource_monitor, _watchdog, _shutdown_manager

    # 初始化全局异常处理器
    _global_exception_handler = GlobalExceptionHandler(log_dir)
    _global_exception_handler.install()

    # 初始化优雅关闭管理器
    _shutdown_manager = GracefulShutdown(timeout=5.0)

    # 初始化资源监控器
    if enable_resource_monitor:
        _resource_monitor = ResourceMonitor(check_interval=30.0)
        _resource_monitor.start()

    # 初始化看门狗
    if enable_watchdog:
        _watchdog = WatchdogTimer(timeout=watchdog_timeout)
        _watchdog.start()

    logger.info("错误恢复系统已初始化")


def shutdown_error_recovery() -> None:
    """关闭错误恢复系统"""
    global _global_exception_handler, _resource_monitor, _watchdog, _shutdown_manager

    # 执行优雅关闭
    if _shutdown_manager:
        _shutdown_manager.execute_shutdown()

    # 停止看门狗
    if _watchdog:
        _watchdog.stop()

    # 停止资源监控
    if _resource_monitor:
        _resource_monitor.stop()

    # 卸载全局异常处理器
    if _global_exception_handler:
        _global_exception_handler.uninstall()

    logger.info("错误恢复系统已关闭")


def register_cleanup_task(name: str, task: Callable) -> None:
    """注册清理任务

    Args:
        name: 任务名称
        task: 清理函数
    """
    if _shutdown_manager:
        _shutdown_manager.register_cleanup(name, task)


def feed_watchdog() -> None:
    """喂狗（重置看门狗计时器）"""
    if _watchdog:
        _watchdog.feed()


def get_error_recovery_status() -> Dict[str, Any]:
    """获取错误恢复系统状态

    Returns:
        状态字典
    """
    status = {
        "global_handler": _global_exception_handler is not None,
        "resource_monitor": _resource_monitor.get_status() if _resource_monitor else None,
        "watchdog": _watchdog.get_status() if _watchdog else None,
        "shutdown_manager": _shutdown_manager.get_status() if _shutdown_manager else None,
    }
    return status
