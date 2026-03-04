"""
日志系统测试
"""

import logging
import tempfile
from pathlib import Path

import pytest

from dev_bot.logger import (
    DevBotLogger,
    close_logging,
    critical,
    debug,
    error,
    exception,
    get_logger,
    info,
    set_log_level,
    setup_logging,
    warning,
)


@pytest.fixture(autouse=True)
def reset_logger():
    """每个测试前重置日志系统"""
    # 关闭现有日志系统
    close_logging()

    # 重置全局实例
    from dev_bot.logger import _global_logger
    _global_logger._initialized = False
    _global_logger.loggers = {}
    _global_logger.log_level = logging.INFO
    _global_logger.log_dir = None
    _global_logger.file_handler = None

    yield

    # 测试后清理
    close_logging()


def test_logger_singleton():
    """测试日志记录器单例模式"""
    logger1 = DevBotLogger()
    logger2 = DevBotLogger()

    assert logger1 is logger2


def test_setup_logging_console():
    """测试设置控制台日志"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)

        setup_logging(
            log_level=logging.DEBUG,
            log_dir=log_dir,
            enable_console=True,
            enable_file=False
        )

        logger = get_logger("test")
        assert logger is not None
        assert logger.level == logging.DEBUG


def test_setup_logging_file():
    """测试设置文件日志"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)

        setup_logging(
            log_level=logging.INFO,
            log_dir=log_dir,
            enable_console=False,
            enable_file=True,
            log_file="test.log"
        )

        logger = get_logger("test")
        assert logger is not None

        # 日志文件可能尚未创建，因为还没有写入日志


def test_get_logger():
    """测试获取日志记录器"""
    logger1 = get_logger("module1")
    logger2 = get_logger("module2")

    assert logger1 is not logger2
    assert logger1.name == "module1"
    assert logger2.name == "module2"


def test_get_logger_same_name():
    """测试获取相同名称的日志记录器"""
    logger1 = get_logger("same_name")
    logger2 = get_logger("same_name")

    assert logger1 is logger2


def test_set_log_level():
    """测试设置日志级别"""
    setup_logging(log_level=logging.INFO)

    logger = get_logger("test")
    assert logger.level == logging.INFO

    set_log_level(logging.DEBUG)
    assert logger.level == logging.DEBUG

    set_log_level("ERROR")
    assert logger.level == logging.ERROR


def test_log_levels():
    """测试不同日志级别"""
    setup_logging(log_level=logging.DEBUG)

    logger = get_logger("test")

    # 这些应该不会抛出异常
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")


def test_convenience_functions():
    """测试便捷函数"""
    setup_logging(log_level=logging.INFO)

    # 这些应该不会抛出异常
    debug("Debug message")
    info("Info message")
    warning("Warning message")
    error("Error message")
    critical("Critical message")


def test_exception_logging():
    """测试异常日志记录"""
    setup_logging(log_level=logging.ERROR)

    try:
        _ = 1 / 0
    except Exception:
        # exception 应该记录异常和堆栈跟踪
        exception("Division by zero occurred")


def test_log_file_creation():
    """测试日志文件创建"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)

        setup_logging(
            log_level=logging.INFO,
            log_dir=log_dir,
            enable_console=False,
            enable_file=True,
            log_file="test_creation.log"
        )

        logger = get_logger("test")
        logger.info("Test message")

        # 关闭日志以确保缓冲区刷新
        close_logging()

        # 检查日志文件是否存在
        log_file = log_dir / "test_creation.log"
        assert log_file.exists()

        # 检查日志内容
        content = log_file.read_text(encoding='utf-8')
        assert "Test message" in content


def test_log_file_rotation():
    """测试日志文件轮转"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)

        # 使用小的文件大小限制来测试轮转
        setup_logging(
            log_level=logging.INFO,
            log_dir=log_dir,
            enable_console=False,
            enable_file=True,
            log_file="test_rotation.log",
            max_file_size=1024,  # 1KB
            backup_count=3
        )

        logger = get_logger("test")

        # 写入大量日志以触发轮转
        for i in range(100):
            logger.info(f"Test message {i}: " + "x" * 100)

        close_logging()

        # 检查是否有多个日志文件
        log_files = list(log_dir.glob("test_rotation.log*"))
        assert len(log_files) > 1


def test_custom_log_format():
    """测试自定义日志格式"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)

        custom_format = '%(levelname)s - %(message)s'

        setup_logging(
            log_level=logging.INFO,
            log_dir=log_dir,
            log_format=custom_format,
            enable_console=False,
            enable_file=True
        )

        logger = get_logger("test")
        logger.info("Test message")

        close_logging()

        # 检查日志文件
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            content = log_files[0].read_text(encoding='utf-8')
            assert "INFO - Test message" in content


def test_multiple_loggers():
    """测试多个日志记录器"""
    setup_logging(log_level=logging.DEBUG)

    logger1 = get_logger("module1")
    logger2 = get_logger("module2")
    logger3 = get_logger("module3")

    logger1.debug("Debug from module1")
    logger2.info("Info from module2")
    logger3.warning("Warning from module3")


def test_logger_context():
    """测试日志记录器上下文"""
    setup_logging(log_level=logging.INFO)

    logger = get_logger("test.module")

    # 使用 extra 参数添加上下文信息
    logger.info("Message with context", extra={'user': 'test_user'})


def test_close_logging():
    """测试关闭日志系统"""
    setup_logging(
        log_level=logging.INFO,
        enable_console=True
    )

    logger = get_logger("test")
    logger.info("Before close")

    close_logging()

    # 关闭后应该仍然可以获取日志记录器，但不会有处理器
    logger2 = get_logger("test2")
    assert logger2 is not None


def test_default_configuration():
    """测试默认配置"""
    # 不调用 setup_logging，使用默认配置
    logger = get_logger("test")

    # 应该能够记录日志而不会崩溃
    logger.info("Test message with default config")


def test_invalid_log_level_string():
    """测试无效的日志级别字符串"""
    setup_logging()

    # 无效的日志级别字符串应该回退到默认值
    set_log_level("INVALID_LEVEL")

    logger = get_logger("test")
    # 日志记录器应该仍然工作
    logger.info("Test message after invalid level")


def test_log_directory_creation():
    """测试日志目录自动创建"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / "nested" / "logs" / "dir"

        setup_logging(
            log_level=logging.INFO,
            log_dir=log_dir,
            enable_console=False,
            enable_file=True
        )

        # 目录应该已创建
        assert log_dir.exists()
        assert log_dir.is_dir()

        logger = get_logger("test")
        logger.info("Test message")

        close_logging()

        # 检查日志文件
        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) > 0


def test_unicode_logging():
    """测试 Unicode 字符日志"""
    setup_logging(log_level=logging.INFO)

    logger = get_logger("test")

    # 记录包含 Unicode 字符的消息
    logger.info("测试中文日志 🎉")
    logger.info("Emoji test: ✅ ❌ ⚠️ 🚀")
    logger.info("日本語テスト")
    logger.info("한국어 테스트")


def test_long_message():
    """测试长消息日志"""
    setup_logging(log_level=logging.INFO)

    logger = get_logger("test")

    # 创建长消息
    long_message = "A" * 10000
    logger.info(long_message)


def test_structured_logging():
    """测试结构化日志"""
    setup_logging(log_level=logging.INFO)

    logger = get_logger("test")

    # 使用 JSON 格式的消息
    import json
    data = {"key": "value", "number": 42}
    logger.info(json.dumps(data))


def test_performance():
    """测试日志性能"""
    import time

    setup_logging(log_level=logging.INFO)

    logger = get_logger("test")

    # 记录大量日志消息
    start_time = time.time()
    for i in range(1000):
        logger.info(f"Message {i}")
    end_time = time.time()

    elapsed = end_time - start_time
    # 应该在合理时间内完成（例如 < 1 秒）
    assert elapsed < 5.0, f"Logging 1000 messages took {elapsed:.2f} seconds"
