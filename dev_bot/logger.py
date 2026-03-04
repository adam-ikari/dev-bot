"""
统一的日志记录系统

提供统一的日志接口，支持：
- 多级别日志（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- 格式化输出
- 文件和控制台输出
- 日志轮转
- 上下文信息
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


class DevBotLogger:
    """Dev-Bot 统一日志记录器"""

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化日志系统（仅执行一次）"""
        if not DevBotLogger._initialized:
            self.loggers = {}
            self.log_level = logging.INFO
            self.log_format = None
            self.date_format = None
            self.log_dir = None
            self.file_handler = None
            DevBotLogger._initialized = True

    def setup(
        self,
        log_level: Union[str, int] = logging.INFO,
        log_format: Optional[str] = None,
        date_format: Optional[str] = None,
        log_dir: Optional[Union[str, Path]] = None,
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        配置日志系统

        Args:
            log_level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
            log_format: 日志格式字符串
            date_format: 日期格式字符串
            log_dir: 日志文件目录
            log_file: 日志文件名（如果未指定，使用默认名称）
            enable_console: 是否启用控制台输出
            enable_file: 是否启用文件输出
            max_file_size: 单个日志文件最大大小（字节）
            backup_count: 保留的日志文件备份数量
        """
        # 转换日志级别
        if isinstance(log_level, str):
            self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        else:
            self.log_level = log_level

        # 设置默认格式
        if log_format is None:
            log_format = '[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s'

        if date_format is None:
            date_format = '%Y-%m-%d %H:%M:%S'

        self.log_format = log_format
        self.date_format = date_format

        # 设置日志目录
        if log_dir is not None:
            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.log_dir = None

        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # 清除现有的处理器
        root_logger.handlers.clear()

        # 添加控制台处理器
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_formatter = logging.Formatter(log_format, date_format)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        # 添加文件处理器
        if enable_file and self.log_dir is not None:
            if log_file is None:
                log_file = f"dev-bot_{datetime.now().strftime('%Y%m%d')}.log"

            log_path = self.log_dir / log_file

            # 使用 RotatingFileHandler 进行日志轮转
            from logging.handlers import RotatingFileHandler
            self.file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            self.file_handler.setLevel(self.log_level)
            file_formatter = logging.Formatter(log_format, date_format)
            self.file_handler.setFormatter(file_formatter)
            root_logger.addHandler(self.file_handler)

        DevBotLogger._initialized = True

    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器

        Args:
            name: 日志记录器名称（通常使用 __name__）

        Returns:
            logging.Logger 实例
        """
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
            self.loggers[name].setLevel(self.log_level)
        return self.loggers[name]

    def set_level(self, level: Union[str, int]):
        """
        设置日志级别

        Args:
            level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        """
        if isinstance(level, str):
            self.log_level = getattr(logging, level.upper(), logging.INFO)
        else:
            self.log_level = level

        # 更新所有日志记录器的级别
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        for logger in self.loggers.values():
            logger.setLevel(self.log_level)

        # 更新处理器的级别
        for handler in root_logger.handlers:
            handler.setLevel(self.log_level)

    def close(self):
        """关闭日志系统"""
        if self.file_handler is not None:
            self.file_handler.close()

        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler.close()


# 全局日志记录器实例
_global_logger = DevBotLogger()


def setup_logging(
    log_level: Union[str, int] = logging.INFO,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
    log_dir: Optional[Union[str, Path]] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = False,
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5
):
    """
    配置全局日志系统

    Args:
        log_level: 日志级别
        log_format: 日志格式字符串
        date_format: 日期格式字符串
        log_dir: 日志文件目录
        log_file: 日志文件名
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
        max_file_size: 单个日志文件最大大小（字节）
        backup_count: 保留的日志文件备份数量
    """
    _global_logger.setup(
        log_level=log_level,
        log_format=log_format,
        date_format=date_format,
        log_dir=log_dir,
        log_file=log_file,
        enable_console=enable_console,
        enable_file=enable_file,
        max_file_size=max_file_size,
        backup_count=backup_count
    )


def get_logger(name: str = 'dev-bot') -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger 实例
    """
    return _global_logger.get_logger(name)


def set_log_level(level: Union[str, int]):
    """
    设置日志级别

    Args:
        level: 日志级别
    """
    _global_logger.set_level(level)


def close_logging():
    """关闭日志系统"""
    _global_logger.close()


# 便捷函数
def debug(message: str, *args, **kwargs):
    """记录 DEBUG 级别日志"""
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """记录 INFO 级别日志"""
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """记录 WARNING 级别日志"""
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """记录 ERROR 级别日志"""
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """记录 CRITICAL 级别日志"""
    get_logger().critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    """记录异常信息（自动包含堆栈跟踪）"""
    get_logger().exception(message, *args, **kwargs)


# 模块级日志记录器
logger = get_logger(__name__)


if __name__ == "__main__":
    # 演示使用
    setup_logging(
        log_level=logging.DEBUG,
        log_dir=Path.cwd() / "logs",
        enable_file=True
    )

    logger = get_logger("demo")

    logger.debug("这是一条 DEBUG 消息")
    logger.info("这是一条 INFO 消息")
    logger.warning("这是一条 WARNING 消息")
    logger.error("这是一条 ERROR 消息")
    logger.critical("这是一条 CRITICAL 消息")

    try:
        _ = 1 / 0
    except Exception:
        logger.exception("发生异常")

    # 使用便捷函数
    info("使用便捷函数记录日志")
    error("这是一条错误消息")

    close_logging()
