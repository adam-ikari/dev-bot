import json
import tempfile
from pathlib import Path

import pytest

from dev_bot.main import Config


@pytest.fixture
def temp_config():
    """创建临时配置文件"""
    config_data = {
        "ai_command": "iflow",
        "prompt_file": "PROMPT.md",
        "timeout": 300
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    Path(temp_path).unlink(missing_ok=True)


def test_config_load(temp_config):
    """测试配置加载"""
    config = Config(temp_config)
    assert config.get('ai_command') == 'iflow'
    assert config.get('prompt_file') == 'PROMPT.md'
    assert config.get('timeout') == 300


def test_config_get_default():
    """测试获取配置默认值"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"ai_command": "test", "prompt_file": "PROMPT.md"}, f)
        temp_path = f.name

    try:
        config = Config(temp_path)
        assert config.get('nonexistent', 'default') == 'default'
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_config_ai_command(temp_config):
    """测试获取 AI 命令"""
    config = Config(temp_config)
    assert config.get_ai_command() == 'iflow'


def test_config_timeout(temp_config):
    """测试获取超时时间"""
    config = Config(temp_config)
    assert config.get_timeout() == 300
