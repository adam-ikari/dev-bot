#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .core import DevBotCore, create_bot
from .auto_restart import AutoRestartManager, get_restart_manager
from .tech_stack_detector import (
    TechStackDetector,
    detect_tech_stack,
    generate_tech_stack_report,
)

__version__ = "2.0.0"
__all__ = [
    "DevBotCore",
    "create_bot",
    "AutoRestartManager",
    "get_restart_manager",
    "TechStackDetector",
    "detect_tech_stack",
    "generate_tech_stack_report"
]