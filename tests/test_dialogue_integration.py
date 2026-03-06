"""测试对话整合功能"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from dev_bot.dialogue_integrator import DialogueIntegrator, get_dialogue_integrator, reset_dialogue_integrator
from dev_bot.ai_dialogue import DialogueMode


@pytest.fixture
async def dialogue_integrator():
    """创建对话整合器"""
    reset_dialogue_integrator()
    integrator = DialogueIntegrator()
    integrator._initialize()
    return integrator


@pytest.mark.asyncio
async def test_dialogue_integrator_initialization(dialogue_integrator):
    """测试对话整合器初始化"""
    assert dialogue_integrator.dialogue_manager is not None
    assert dialogue_integrator.task_manager is not None
    assert dialogue_integrator.user_role_id == "user"


@pytest.mark.asyncio
async def test_add_user_role(dialogue_integrator):
    """测试添加用户角色"""
    # 用户角色应该已经添加
    assert dialogue_integrator.user_role_id in dialogue_integrator.dialogue_manager.roles
    user_role = dialogue_integrator.dialogue_manager.roles[dialogue_integrator.user_role_id]
    assert user_role.name == "用户"


@pytest.mark.asyncio
async def test_create_dialogue_from_queue(dialogue_integrator):
    """测试从队列创建对话"""
    # 创建一个任务
    task_id = await dialogue_integrator.task_manager.enqueue(
        prompt="测试任务",
        mode="--plan",
        priority=0
    )
    
    # 从任务创建对话
    dialogue_id = await dialogue_integrator.create_dialogue_from_queue(
        task_id=task_id,
        participants=["analyzer", "developer"]
    )
    
    assert dialogue_id is not None
    assert dialogue_integrator.current_dialogue_id == dialogue_id
    
    # 验证对话已创建
    dialogue = dialogue_integrator.dialogue_manager.get_dialogue(dialogue_id)
    assert dialogue is not None
    assert dialogue.topic == "测试任务"
    assert dialogue_integrator.user_role_id in dialogue.participants
    assert "analyzer" in dialogue.participants
    assert "developer" in dialogue.participants


@pytest.mark.asyncio
async def test_create_dialogue_from_nonexistent_task(dialogue_integrator):
    """测试从不存在的任务创建对话"""
    dialogue_id = await dialogue_integrator.create_dialogue_from_queue(
        task_id="nonexistent_task",
        participants=["analyzer"]
    )
    
    assert dialogue_id is None


@pytest.mark.asyncio
async def test_add_user_message_to_current_dialogue(dialogue_integrator):
    """测试向当前对话添加用户消息"""
    # 创建任务和对话
    task_id = await dialogue_integrator.task_manager.enqueue(
        prompt="测试任务",
        mode="--plan",
        priority=0
    )
    dialogue_id = await dialogue_integrator.create_dialogue_from_queue(task_id)
    
    # 添加用户消息
    with patch.object(dialogue_integrator.core, 'call_iflow') as mock_call:
        mock_call.return_value = {
            "success": True,
            "output": "好的，我明白了。"
        }
        
        success = await dialogue_integrator.add_user_message("这是用户的消息")
        
        assert success
        
        # 验证消息已添加
        dialogue = dialogue_integrator.dialogue_manager.get_dialogue(dialogue_id)
        assert len(dialogue.messages) > 0
        assert dialogue.messages[-1].sender_id == dialogue_integrator.user_role_id


@pytest.mark.asyncio
async def test_add_user_message_to_specific_dialogue(dialogue_integrator):
    """测试向指定对话添加用户消息"""
    # 创建两个对话
    task_id1 = await dialogue_integrator.task_manager.enqueue(
        prompt="任务1",
        mode="--plan",
        priority=0
    )
    dialogue_id1 = await dialogue_integrator.create_dialogue_from_queue(task_id1)
    
    task_id2 = await dialogue_integrator.task_manager.enqueue(
        prompt="任务2",
        mode="--plan",
        priority=0
    )
    dialogue_id2 = await dialogue_integrator.create_dialogue_from_queue(task_id2)
    
    # 向第二个对话添加消息
    with patch.object(dialogue_integrator.core, 'call_iflow') as mock_call:
        mock_call.return_value = {
            "success": True,
            "output": "收到消息。"
        }
        
        success = await dialogue_integrator.add_user_message(
            content="消息",
            dialogue_id=dialogue_id2
        )
        
        assert success
        
        # 验证消息添加到正确的对话
        dialogue2 = dialogue_integrator.dialogue_manager.get_dialogue(dialogue_id2)
        assert len(dialogue2.messages) > 0


@pytest.mark.asyncio
async def test_add_user_message_without_dialogue(dialogue_integrator):
    """测试在没有活跃对话时添加消息"""
    success = await dialogue_integrator.add_user_message("测试消息")
    
    assert not success


@pytest.mark.asyncio
async def test_list_dialogues(dialogue_integrator):
    """测试列出所有对话"""
    # 创建两个对话
    task_id1 = await dialogue_integrator.task_manager.enqueue(
        prompt="任务1",
        mode="--plan",
        priority=0
    )
    dialogue_id1 = await dialogue_integrator.create_dialogue_from_queue(task_id1)
    
    task_id2 = await dialogue_integrator.task_manager.enqueue(
        prompt="任务2",
        mode="--plan",
        priority=0
    )
    dialogue_id2 = await dialogue_integrator.create_dialogue_from_queue(task_id2)
    
    # 列出所有对话（获取所有对话并过滤）
    all_dialogues = await dialogue_integrator.list_dialogues()
    dialogues = [d for d in all_dialogues if d.dialogue_id in [dialogue_id1, dialogue_id2]]
    
    assert len(dialogues) == 2
    dialogue_ids = [d.dialogue_id for d in dialogues]
    assert dialogue_id1 in dialogue_ids
    assert dialogue_id2 in dialogue_ids


@pytest.mark.asyncio
async def test_get_dialogue(dialogue_integrator):
    """测试获取对话"""
    # 创建对话
    task_id = await dialogue_integrator.task_manager.enqueue(
        prompt="测试任务",
        mode="--plan",
        priority=0
    )
    dialogue_id = await dialogue_integrator.create_dialogue_from_queue(task_id)
    
    # 获取对话
    dialogue = await dialogue_integrator.get_dialogue(dialogue_id)
    
    assert dialogue is not None
    assert dialogue.dialogue_id == dialogue_id
    assert dialogue.topic == "测试任务"


@pytest.mark.asyncio
async def test_get_nonexistent_dialogue(dialogue_integrator):
    """测试获取不存在的对话"""
    dialogue = await dialogue_integrator.get_dialogue("nonexistent_dialogue")
    
    assert dialogue is None


@pytest.mark.asyncio
async def test_run_dialogue(dialogue_integrator):
    """测试运行对话"""
    # 创建对话
    task_id = await dialogue_integrator.task_manager.enqueue(
        prompt="测试任务",
        mode="--plan",
        priority=0
    )
    dialogue_id = await dialogue_integrator.create_dialogue_from_queue(
        task_id,
        participants=["analyzer"]
    )
    
    # 运行对话（模拟）
    with patch.object(dialogue_integrator.dialogue_manager, 'start_autonomous_dialogue') as mock_run:
        mock_run.return_value = None  # 不实际运行
        
        success = await dialogue_integrator.run_dialogue(dialogue_id, max_duration=10)
        
        assert success
        mock_run.assert_called_once_with(dialogue_id, max_duration=10)


@pytest.mark.asyncio
async def test_run_nonexistent_dialogue(dialogue_integrator):
    """测试运行不存在的对话"""
    success = await dialogue_integrator.run_dialogue("nonexistent_dialogue")
    
    assert not success


@pytest.mark.asyncio
async def test_get_dialogue_status(dialogue_integrator):
    """测试获取对话状态"""
    # 创建对话
    task_id = await dialogue_integrator.task_manager.enqueue(
        prompt="测试任务",
        mode="--plan",
        priority=0
    )
    dialogue_id = await dialogue_integrator.create_dialogue_from_queue(task_id)
    
    # 获取状态
    status = await dialogue_integrator.get_dialogue_status()
    
    assert "current_dialogue_id" in status
    assert "dialogue_manager_status" in status
    assert "task_manager_status" in status
    assert status["current_dialogue_id"] == dialogue_id


@pytest.mark.asyncio
async def test_global_dialogue_integrator():
    """测试全局对话整合器"""
    reset_dialogue_integrator()
    
    # 获取实例
    integrator1 = get_dialogue_integrator()
    integrator2 = get_dialogue_integrator()
    
    # 应该是同一个实例
    assert integrator1 is integrator2
    
    # 重置后应该是新实例
    reset_dialogue_integrator()
    integrator3 = get_dialogue_integrator()
    
    assert integrator1 is not integrator3