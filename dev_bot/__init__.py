#!/usr/bin/env python3

from .core import get_core, DevBotCore
from .logger import (
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
from .tech_stack_detector import (
    TechStackDetector,
    detect_tech_stack,
    generate_tech_stack_report,
)

__version__ = "3.0.0"
__all__ = [
    "get_core",
    "DevBotCore",
    "TechStackDetector",
    "detect_tech_stack",
    "generate_tech_stack_report",
    # 日志系统
    "setup_logging",
    "get_logger",
    "set_log_level",
    "close_logging",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "exception",
]
