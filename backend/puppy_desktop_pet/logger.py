"""
小黑狗桌宠日志模块
提供统一的日志配置和获取接口
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional


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

# 全局日志配置标记
_configured = False


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
