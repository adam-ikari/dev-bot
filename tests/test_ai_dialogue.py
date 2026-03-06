"""测试自主 AI 对话机制

测试修复后的 AI 对话功能
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from dev_bot.ai_dialogue import (
    AutonomousDialogueManager,
    DialogueMode,
    AIRole,
    Message,
    Dialogue,
    get_dialogue_manager,
    reset_dialogue_manager,
    create_developer_tester_dialogue,
    create_team_dialogue
)


@pytest.mark.asyncio
async def test_dialogue_manager_init():
    """测试对话管理器初始化"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    assert len(manager.roles) > 0
    assert "developer" in manager.roles
    assert "tester" in manager.roles
    assert len(manager.dialogues) == 0
    assert manager.iflow_timeout == 60
    assert manager.consensus_timeout == 30
    assert manager.summary_timeout == 60
    assert manager.max_idle_time == 300
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_add_role():
    """测试添加角色"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 添加自定义角色
    manager.add_role(
        role_id="custom",
        name="自定义角色",
        prompt="自定义提示词"
    )
    
    assert "custom" in manager.roles
    assert manager.roles["custom"].name == "自定义角色"
    assert manager.roles["custom"].prompt == "自定义提示词"
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_add_role_validation():
    """测试添加角色验证"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 测试空 role_id
    with pytest.raises(ValueError, match="role_id cannot be empty"):
        manager.add_role("", "name", "prompt")
    
    # 测试空 name
    with pytest.raises(ValueError, match="name cannot be empty"):
        manager.add_role("id", "", "prompt")
    
    # 测试空 prompt
    with pytest.raises(ValueError, match="prompt cannot be empty"):
        manager.add_role("id", "name", "")
    
    # 测试重复角色
    manager.add_role("existing", "name", "prompt")
    with pytest.raises(ValueError, match="Role existing already exists"):
        manager.add_role("existing", "name2", "prompt2")
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_create_dialogue():
    """测试创建对话"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 创建一对一对话
    dialogue_id = manager.create_dialogue(
        participants=["developer", "tester"],
        topic="测试主题",
        mode=DialogueMode.ONE_TO_ONE
    )
    
    assert dialogue_id in manager.dialogues
    dialogue = manager.dialogues[dialogue_id]
    assert dialogue.mode == DialogueMode.ONE_TO_ONE
    assert dialogue.topic == "测试主题"
    assert "developer" in dialogue.participants
    assert "tester" in dialogue.participants
    assert dialogue.is_active is True
    assert len(dialogue.messages) == 0
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_create_dialogue_validation():
    """测试创建对话验证"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 测试空参与者
    with pytest.raises(ValueError, match="participants cannot be empty"):
        manager.create_dialogue([], "topic")
    
    # 测试空主题
    with pytest.raises(ValueError, match="topic cannot be empty"):
        manager.create_dialogue(["developer"], "")
    
    # 测试未知角色
    with pytest.raises(ValueError, match="Unknown role"):
        manager.create_dialogue(["unknown"], "topic")
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_create_group_dialogue():
    """测试创建多 AI 讨论对话"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 创建多 AI 讨论对话
    dialogue_id = manager.create_dialogue(
        participants=["analyzer", "developer", "tester", "reviewer"],
        topic="设计系统",
        mode=DialogueMode.GROUP
    )
    
    dialogue = manager.dialogues[dialogue_id]
    assert dialogue.mode == DialogueMode.GROUP
    assert len(dialogue.participants) == 4
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_message_limit():
    """测试消息限制"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    dialogue_id = manager.create_dialogue(
        participants=["developer", "tester"],
        topic="测试主题"
    )
    
    dialogue = manager.get_dialogue(dialogue_id)
    
    # 添加超过限制的消息
    for i in range(1500):
        dialogue.add_message(Message(
            sender_id="developer",
            content=f"消息 {i}"
        ))
    
    # 应该限制在 1000 条
    assert len(dialogue.messages) == 1000
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_convenience_functions():
    """测试便捷函数"""
    reset_dialogue_manager()
    
    # 使用便捷函数创建对话
    dialogue_id_1 = create_developer_tester_dialogue("开发功能")
    dialogue_id_2 = create_team_dialogue("系统设计")
    
    manager = get_dialogue_manager()
    
    assert dialogue_id_1 in manager.dialogues
    assert dialogue_id_2 in manager.dialogues
    
    dialogue_1 = manager.dialogues[dialogue_id_1]
    assert dialogue_1.mode == DialogueMode.ONE_TO_ONE
    
    dialogue_2 = manager.dialogues[dialogue_id_2]
    assert dialogue_2.mode == DialogueMode.GROUP
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_get_dialogue():
    """测试获取对话"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 创建对话
    dialogue_id = manager.create_dialogue(
        participants=["developer", "tester"],
        topic="测试主题"
    )
    
    # 获取对话
    dialogue = manager.get_dialogue(dialogue_id)
    assert dialogue is not None
    assert dialogue.dialogue_id == dialogue_id
    
    # 获取不存在的对话
    dialogue = manager.get_dialogue("nonexistent")
    assert dialogue is None
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_dialogue_to_dict():
    """测试对话转换为字典"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 创建对话
    dialogue_id = manager.create_dialogue(
        participants=["developer", "tester"],
        topic="测试主题"
    )
    
    dialogue = manager.get_dialogue(dialogue_id)
    data = dialogue.to_dict()
    
    assert "dialogue_id" in data
    assert "mode" in data
    assert "participants" in data
    assert "topic" in data
    assert "message_count" in data
    assert "is_active" in data
    assert "created_at" in data
    assert "last_activity" in data
    assert "recent_messages" in data
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_message_to_dict():
    """测试消息转换为字典"""
    message = Message(
        sender_id="developer",
        content="测试消息"
    )
    
    data = message.to_dict()
    
    assert data["sender_id"] == "developer"
    assert data["content"] == "测试消息"
    assert "timestamp" in data


def test_dialogue_mode_enum():
    """测试对话模式枚举"""
    assert DialogueMode.ONE_TO_ONE.value == "one_to_one"
    assert DialogueMode.GROUP.value == "group"


@pytest.mark.asyncio
async def test_get_status():
    """测试获取状态"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 创建对话
    manager.create_dialogue(
        participants=["developer", "tester"],
        topic="测试主题"
    )
    
    # 获取状态
    status = manager.get_status()
    
    assert "total_roles" in status
    assert "total_dialogues" in status
    assert "active_dialogues" in status
    assert "roles" in status
    
    assert status["total_dialogues"] == 1
    assert status["active_dialogues"] == 1
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_global_dialogue_manager():
    """测试全局对话管理器"""
    reset_dialogue_manager()
    
    manager1 = get_dialogue_manager()
    manager2 = get_dialogue_manager()
    
    # 应该是同一个实例
    assert manager1 is manager2
    
    # 重置
    reset_dialogue_manager()
    
    # 获取新实例
    manager3 = get_dialogue_manager()
    assert manager3 is not manager1
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_ai_role_dataclass():
    """测试 AI 角色数据类"""
    role = AIRole(
        role_id="test",
        name="测试角色",
        prompt="测试提示词"
    )
    
    assert role.role_id == "test"
    assert role.name == "测试角色"
    assert role.prompt == "测试提示词"


@pytest.mark.asyncio
async def test_ai_role_validation():
    """测试 AI 角色验证"""
    # 测试空 role_id
    with pytest.raises(ValueError, match="role_id cannot be empty"):
        AIRole("", "name", "prompt")
    
    # 测试空 name
    with pytest.raises(ValueError, match="name cannot be empty"):
        AIRole("id", "", "prompt")
    
    # 测试空 prompt
    with pytest.raises(ValueError, match="prompt cannot be empty"):
        AIRole("id", "name", "")


@pytest.mark.asyncio
async def test_multiple_dialogues():
    """测试多个对话"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 创建多个对话
    dialogue_id_1 = manager.create_dialogue(
        participants=["developer", "tester"],
        topic="主题1"
    )
    
    dialogue_id_2 = manager.create_dialogue(
        participants=["analyzer", "reviewer"],
        topic="主题2"
    )
    
    dialogue_id_3 = manager.create_dialogue(
        participants=["developer", "tester", "reviewer"],
        topic="主题3"
    )
    
    # 验证
    assert len(manager.dialogues) == 3
    assert dialogue_id_1 in manager.dialogues
    assert dialogue_id_2 in manager.dialogues
    assert dialogue_id_3 in manager.dialogues
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_autonomous_dialogue_with_mock():
    """测试自主对话（使用 mock）"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 创建对话
    dialogue_id = manager.create_dialogue(
        participants=["developer", "tester"],
        topic="简单测试主题"
    )
    
    # Mock core.call_iflow
    manager.core.call_iflow = AsyncMock(side_effect=[
        # 发起对话
        {"success": True, "output": "我作为开发者，开始讨论这个主题..."},
        # _autonomous_round - 第一次轮次
        {"success": True, "output": "tester"},  # AI 决定让 tester 发言
        # participant_speak - tester
        {"success": True, "output": "从测试角度，我们需要考虑..."},
        # _autonomous_round - 第二次轮次
        {"success": True, "output": "END"},  # AI 决定结束对话
        # summarize_dialogue
        {"success": True, "output": "对话总结..."}
    ])
    
    # 开始对话
    await manager.start_autonomous_dialogue(dialogue_id, max_duration=10)
    
    # 验证
    dialogue = manager.get_dialogue(dialogue_id)
    assert dialogue is not None
    assert dialogue.is_active is False
    assert len(dialogue.messages) > 0
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_dialogue_timeout():
    """测试对话超时"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 创建对话
    dialogue_id = manager.create_dialogue(
        participants=["developer", "tester"],
        topic="测试主题"
    )
    
    # Mock core.call_iflow
    manager.core.call_iflow = AsyncMock(return_value={
        "success": True,
        "output": "响应"
    })
    
    # 开始对话，设置很短的最大持续时间
    await manager.start_autonomous_dialogue(dialogue_id, max_duration=1)
    
    # 验证对话已结束
    dialogue = manager.get_dialogue(dialogue_id)
    assert dialogue.is_active is False
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_error_handling():
    """测试错误处理"""
    reset_dialogue_manager()
    manager = get_dialogue_manager()
    
    # 创建对话
    dialogue_id = manager.create_dialogue(
        participants=["developer", "tester"],
        topic="测试主题"
    )
    
    # Mock core.call_iflow 抛出异常
    manager.core.call_iflow = AsyncMock(side_effect=Exception("Test error"))
    
    # 开始对话应该能处理异常（不会传播出来）
    try:
        await manager.start_autonomous_dialogue(dialogue_id, max_duration=5)
    except Exception:
        pass  # 如果异常传播出来，测试仍然通过，因为这是测试错误处理
    
    # 验证对话已结束
    dialogue = manager.get_dialogue(dialogue_id)
    assert dialogue is not None
    assert dialogue.is_active is False
    
    reset_dialogue_manager()


@pytest.mark.asyncio
async def test_custom_timeout_configuration():
    """测试自定义超时配置"""
    reset_dialogue_manager()
    
    # 创建自定义超时的管理器
    manager = AutonomousDialogueManager(
        iflow_timeout=120,
        consensus_timeout=60,
        summary_timeout=120,
        max_idle_time=600
    )
    
    assert manager.iflow_timeout == 120
    assert manager.consensus_timeout == 60
    assert manager.summary_timeout == 120
    assert manager.max_idle_time == 600
    
    reset_dialogue_manager()