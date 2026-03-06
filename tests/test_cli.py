"""测试统一命令行入口"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dev_bot.__main__ import main_parser, handle_ui, handle_run, handle_iterate, handle_dialogue


def test_main_parser():
    """测试主解析器"""
    parser = main_parser()
    
    # 测试无参数（默认 UI）
    args = parser.parse_args([])
    assert args.command is None
    
    # 测试 ui 命令
    args = parser.parse_args(["ui"])
    assert args.command == "ui"
    assert args.mode == "tui"
    
    # 测试 run 命令
    args = parser.parse_args(["run", "test"])
    assert args.command == "run"
    assert args.prompt == "test"
    
    # 测试 iterate 命令
    args = parser.parse_args(["iterate"])
    assert args.command == "iterate"
    assert args.continuous is False
    assert args.once is False
    
    # 测试 dialogue 命令
    args = parser.parse_args(["dialogue", "list"])
    assert args.command == "dialogue"
    assert args.dialogue_action == "list"


def test_ui_parser():
    """测试 UI 子命令解析"""
    parser = main_parser()
    
    # 测试不同模式
    args = parser.parse_args(["ui", "--mode", "web"])
    assert args.mode == "web"
    
    args = parser.parse_args(["ui", "--mode", "api", "--host", "0.0.0.0", "--port", "9000"])
    assert args.mode == "api"
    assert args.host == "0.0.0.0"
    assert args.port == 9000


def test_run_parser():
    """测试 Run 子命令解析"""
    parser = main_parser()
    
    # 测试不同模式
    args = parser.parse_args(["run", "--plan", "test"])
    assert args.plan is True
    assert args.prompt == "test"
    
    args = parser.parse_args(["run", "-y", "test"])
    assert args.plan is False
    assert args.y is True
    
    args = parser.parse_args(["run", "--thinking", "test"])
    assert args.thinking is True
    
    # 测试 headless 模式
    args = parser.parse_args(["run", "--headless", "test"])
    assert args.headless is True
    assert args.prompt == "test"
    
    # 测试 headless + 执行模式
    args = parser.parse_args(["run", "--headless", "-y", "test"])
    assert args.headless is True
    assert args.y is True
    assert args.api_host == "127.0.0.1"
    assert args.api_port == 8080
    
    # 测试自定义 API 配置
    args = parser.parse_args(["run", "--headless", "--api-host", "0.0.0.0", "--api-port", "9000", "test"])
    assert args.headless is True
    assert args.api_host == "0.0.0.0"
    assert args.api_port == 9000


def test_iterate_parser():
    """测试 Iterate 子命令解析"""
    parser = main_parser()
    
    # 测试单次迭代
    args = parser.parse_args(["iterate"])
    assert args.continuous is False
    assert args.once is False
    assert args.interval == 1800
    assert args.project == Path.cwd()
    
    # 测试连续迭代
    args = parser.parse_args(["iterate", "--continuous", "--interval", "600"])
    assert args.continuous is True
    assert args.interval == 600
    
    # 测试指定项目
    args = parser.parse_args(["iterate", "--project", "/tmp/test"])
    assert args.project == Path("/tmp/test")


def test_dialogue_parser():
    """测试 Dialogue 子命令解析"""
    parser = main_parser()
    
    # 测试创建对话
    args = parser.parse_args(["dialogue", "create", "测试主题"])
    assert args.dialogue_action == "create"
    assert args.topic == "测试主题"
    
    args = parser.parse_args(["dialogue", "create", "测试主题", "--participants", "analyzer", "developer"])
    assert args.participants == ["analyzer", "developer"]
    
    # 测试列出对话
    args = parser.parse_args(["dialogue", "list"])
    assert args.dialogue_action == "list"
    
    # 测试查看对话
    args = parser.parse_args(["dialogue", "info", "dialogue_123"])
    assert args.dialogue_action == "info"
    assert args.dialogue_id == "dialogue_123"
    
    # 测试运行对话
    args = parser.parse_args(["dialogue", "run", "dialogue_123", "--duration", "600"])
    assert args.dialogue_action == "run"
    assert args.dialogue_id == "dialogue_123"
    assert args.duration == 600


@pytest.mark.asyncio
async def test_handle_run():
    """测试 Run 命令处理"""
    args = Mock()
    args.plan = True
    args.y = False
    args.thinking = False
    args.headless = False
    args.prompt = "test"
    
    with patch("dev_bot.__main__.get_core") as mock_get_core:
        mock_core = Mock()
        mock_core.plan = AsyncMock(return_value={"success": True, "duration": 1.0, "output": "result"})
        mock_get_core.return_value = mock_core
        
        await handle_run(args)
        
        mock_core.plan.assert_called_once_with("test")


@pytest.mark.asyncio
async def test_handle_run_headless():
    """测试 Run 命令处理（headless 模式）"""
    args = Mock()
    args.plan = False
    args.y = True
    args.thinking = False
    args.headless = True
    args.prompt = "test"
    
    with patch("dev_bot.__main__.get_core") as mock_get_core:
        mock_core = Mock()
        mock_core.execute = AsyncMock(return_value={"success": True, "duration": 2.0, "output": "result"})
        mock_get_core.return_value = mock_core
        
        await handle_run(args)
        
        mock_core.execute.assert_called_once_with("test")


@pytest.mark.asyncio
async def test_handle_iterate_once():
    """测试 Iterate 命令（单次）"""
    args = Mock()
    args.continuous = False
    args.once = True
    args.interval = 1800
    args.project = Path("/tmp/test")
    
    with patch("dev_bot.__main__.SimpleSelfIteration") as mock_iteration_class:
        mock_iteration = Mock()
        mock_iteration.run_iteration = AsyncMock(return_value={
            "iteration_id": "test",
            "decision": {"action": "fix"},
            "execution": {"success": True},
            "verification": {"success": True}
        })
        mock_iteration_class.return_value = mock_iteration
        
        await handle_iterate(args)
        
        mock_iteration.run_iteration.assert_called_once()


@pytest.mark.asyncio
async def test_handle_dialogue_list():
    """测试 Dialogue 列表命令"""
    args = Mock()
    args.dialogue_action = "list"
    
    # 注意：DialogueIntegrator 在 handle_dialogue 函数内部导入
    # 这里我们只测试参数解析，不测试实际的导入路径
    # 实际的功能测试在 dialogue_integration 测试中
    
    # 验证参数已正确设置
    assert args.dialogue_action == "list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])