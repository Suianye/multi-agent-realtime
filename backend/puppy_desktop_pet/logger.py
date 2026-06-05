"""
小黑狗桌宠日志模块
提供统一的日志配置和获取接口

增强功能:
    1. 结构化日志输出（JSON 格式可选）
    2. 性能日志（函数执行时间追踪）
    3. 安全日志（敏感信息过滤）
    4. 日志缓冲（批量写入优化）
    5. 崩溃报告集成
"""
import logging
import os
import sys
import re
import json
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
from collections import deque


# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEBUG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
JSON_FORMAT = "%(message)s"

# 全局日志配置标记
_configured = False

# 敏感信息模式（用于过滤）
_SENSITIVE_PATTERNS = [
    (re.compile(r'password["\s:=]+\S+', re.IGNORECASE), 'password=***'),
    (re.compile(r'token["\s:=]+\S+', re.IGNORECASE), 'token=***'),
    (re.compile(r'secret["\s:=]+\S+', re.IGNORECASE), 'secret=***'),
    (re.compile(r'api[_-]?key["\s:=]+\S+', re.IGNORECASE), 'api_key=***'),
    (re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'), '****-****-****-****'),  # 信用卡
]

# 性能日志缓冲
_performance_buffer: deque = deque(maxlen=1000)
_buffer_lock = threading.Lock()


def setup_logging(
    level: str = "INFO",
    log_to_file: bool = True,
    log_dir: str = "logs",
    max_file_size: int = 5 * 1024 * 1024,  # 5MB
    backup_count: int = 3,
    debug_mode: bool = False,
) -> None:
    """配置全局日志系统

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: 是否输出到文件
        log_dir: 日志文件目录
        max_file_size: 单个日志文件最大大小（字节）
        backup_count: 保留的备份日志文件数量
        debug_mode: 是否启用调试模式（显示更详细的日志格式）
    """
    global _configured

    # 验证日志级别
    if level.upper() not in LOG_LEVELS:
        print(f"警告: 无效的日志级别 '{level}'，使用默认级别 INFO")
        level = "INFO"

    log_level = LOG_LEVELS[level.upper()]
    log_format = DEBUG_FORMAT if debug_mode else DEFAULT_FORMAT

    # 创建根日志记录器
    root_logger = logging.getLogger("puppy_desktop_pet")
    root_logger.setLevel(log_level)

    # 清除现有处理器（避免重复配置）
    root_logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 文件处理器（可选）
    if log_to_file:
        try:
            # 确保日志目录存在
            os.makedirs(log_dir, exist_ok=True)

            # 生成日志文件名（按日期）
            date_str = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(log_dir, f"puppy_{date_str}.log")

            # 使用 RotatingFileHandler 实现日志轮转
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(log_format)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

            root_logger.debug(f"日志文件: {log_file}")

        except (OSError, PermissionError) as e:
            root_logger.warning(f"无法创建日志文件，仅使用控制台输出: {e}")

    _configured = True
    root_logger.info(f"日志系统已初始化 (级别: {level}, 调试模式: {debug_mode})")


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器

    如果日志系统尚未初始化，会自动使用默认配置初始化。

    Args:
        name: 日志记录器名称（通常为模块名）

    Returns:
        logging.Logger: 日志记录器实例
    """
    if not _configured:
        setup_logging()

    # 使用层次化命名
    full_name = f"puppy_desktop_pet.{name}" if not name.startswith("puppy_desktop_pet.") else name
    return logging.getLogger(full_name)


class LogContext:
    """日志上下文管理器

    用于临时更改日志级别或添加额外信息。

    用法:
        with LogContext("my_module", level=logging.DEBUG):
            logger.debug("这条消息会显示")
    """

    def __init__(self, name: str, level: Optional[int] = None):
        self.logger = get_logger(name)
        self.original_level = self.logger.level
        self.new_level = level

    def __enter__(self):
        if self.new_level is not None:
            self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)
        return False


def log_exception(logger: logging.Logger, message: str, exc: Exception) -> None:
    """记录异常信息

    Args:
        logger: 日志记录器
        message: 描述信息
        exc: 异常对象
    """
    logger.error(f"{message}: {type(exc).__name__}: {exc}", exc_info=True)


def log_boundary_violation(logger: logging.Logger, param_name: str,
                            value: any, min_val: any = None,
                            max_val: any = None) -> None:
    """记录边界违规

    Args:
        logger: 日志记录器
        param_name: 参数名称
        value: 实际值
        min_val: 最小允许值
        max_val: 最大允许值
    """
    if min_val is not None and max_val is not None:
        logger.warning(f"参数 '{param_name}' 值 {value} 超出范围 [{min_val}, {max_val}]")
    elif min_val is not None:
        logger.warning(f"参数 '{param_name}' 值 {value} 小于最小值 {min_val}")
    elif max_val is not None:
        logger.warning(f"参数 '{param_name}' 值 {value} 大于最大值 {max_val}")
    else:
        logger.warning(f"参数 '{param_name}' 值 {value} 无效")


def sanitize_log_message(message: str) -> str:
    """过滤日志消息中的敏感信息

    Args:
        message: 原始消息

    Returns:
        过滤后的消息
    """
    for pattern, replacement in _SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


class SensitiveFilter(logging.Filter):
    """敏感信息过滤器

    自动过滤日志中的密码、token、API key 等敏感信息。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录

        Args:
            record: 日志记录

        Returns:
            是否允许该记录通过
        """
        if isinstance(record.msg, str):
            record.msg = sanitize_log_message(record.msg)
        if record.args and isinstance(record.args, dict):
            for key, value in record.args.items():
                if isinstance(value, str):
                    record.args[key] = sanitize_log_message(value)
        return True


class JsonFormatter(logging.Formatter):
    """JSON 格式化器

    将日志记录格式化为 JSON 结构，便于日志分析和聚合。
    """

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON

        Args:
            record: 日志记录

        Returns:
            JSON 格式的日志字符串
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # 添加额外字段
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


def log_performance(logger: logging.Logger, operation: str,
                    duration: float, details: Dict[str, Any] = None) -> None:
    """记录性能日志

    Args:
        logger: 日志记录器
        operation: 操作名称
        duration: 执行时间（秒）
        details: 额外详情
    """
    entry = {
        "timestamp": time.time(),
        "operation": operation,
        "duration_ms": round(duration * 1000, 2),
    }
    if details:
        entry["details"] = details

    with _buffer_lock:
        _performance_buffer.append(entry)

    # 只在超过阈值时记录
    if duration > 1.0:
        logger.warning(f"性能警告: {operation} 耗时 {duration:.2f}s")
    elif duration > 0.1:
        logger.debug(f"性能日志: {operation} 耗时 {duration:.3f}s")


def get_performance_stats() -> List[Dict[str, Any]]:
    """获取性能统计

    Returns:
        性能日志列表
    """
    with _buffer_lock:
        return list(_performance_buffer)


def performance_timer(logger: logging.Logger = None, operation: str = None):
    """性能计时装饰器

    Args:
        logger: 日志记录器（可选）
        operation: 操作名称（可选，默认使用函数名）

    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if logger:
                    log_performance(logger, op_name, duration)
        return wrapper
    return decorator


class LogManager:
    """日志管理器

    提供日志系统的高级管理功能。
    """

    _instance: Optional['LogManager'] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers: List[logging.Handler] = []
        self._filters: List[logging.Filter] = []

    def get_logger(self, name: str) -> logging.Logger:
        """获取或创建日志记录器

        Args:
            name: 日志记录器名称

        Returns:
            日志记录器实例
        """
        if name not in self._loggers:
            full_name = f"puppy_desktop_pet.{name}" if not name.startswith("puppy_desktop_pet.") else name
            self._loggers[name] = logging.getLogger(full_name)
        return self._loggers[name]

    def add_global_filter(self, filter_func: logging.Filter) -> None:
        """添加全局过滤器

        Args:
            filter_func: 过滤器实例
        """
        self._filters.append(filter_func)
        # 添加到所有已注册的日志记录器
        for logger in self._loggers.values():
            logger.addFilter(filter_func)

    def get_all_loggers(self) -> Dict[str, logging.Logger]:
        """获取所有已注册的日志记录器

        Returns:
            日志记录器字典
        """
        return self._loggers.copy()

    def set_level_for_all(self, level: str) -> None:
        """设置所有日志记录器的级别

        Args:
            level: 日志级别名称
        """
        log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
        for logger in self._loggers.values():
            logger.setLevel(log_level)


# 全局日志管理器实例
log_manager = LogManager()
