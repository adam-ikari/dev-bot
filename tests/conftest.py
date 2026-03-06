"""
pytest 配置文件
"""

import sys
import asyncio
from pathlib import Path

# 将 dev_bot 目录添加到 Python 路径
dev_bot_path = Path(__file__).parent.parent / "dev_bot"
if str(dev_bot_path) not in sys.path:
    sys.path.insert(0, str(dev_bot_path))

# pytest-asyncio 自动模式
import pytest

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
