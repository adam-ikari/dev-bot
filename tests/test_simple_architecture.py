"""测试极简架构

测试基于提示词的任务分配和简化的健康检查
"""
import pytest
import asyncio
from pathlib import Path

from dev_bot.prompt_based_tasks import (
    PromptBasedTaskManager,
    PromptTask,
    get_task_manager,
    reset_task_manager,
    add_developer_task,
    add_tester_task,
    add_reviewer_task,
    add_analyzer_task,
    add_custom_task
)
from dev_bot.simple_guardian import SimpleGuardian, create_guardian


@pytest.mark.asyncio
async def test_prompt_task_creation():
    """测试提示词任务创建"""
    reset_task_manager()
    manager = get_task_manager()
    
    # 添加任务
    task_id = manager.add_task(
        "task_1",
        "测试提示词",
        "测试任务"
    )
    
    assert task_id == "task_1"
    assert "task_1" in manager.tasks
    assert manager.tasks["task_1"].prompt == "测试提示词"
    assert manager.tasks["task_1"].description == "测试任务"
    
    reset_task_manager()


@pytest.mark.asyncio
async def test_add_task_from_template():
    """测试从模板添加任务"""
    reset_task_manager()
    manager = get_task_manager()
    
    # 从模板添加任务
    task_id = manager.add_task_from_template(
        "task_1",
        "developer",
        "实现功能"
    )
    
    assert task_id == "task_1"
    assert "task_1" in manager.tasks
    
    task = manager.tasks["task_1"]
    assert "你是一个开发者" in task.prompt
    assert "实现功能" in task.prompt
    
    reset_task_manager()


@pytest.mark.asyncio
async def test_convenience_functions():
    """测试便捷函数"""
    reset_task_manager()
    
    # 使用便捷函数添加任务
    add_developer_task("dev_1", "开发任务")
    add_tester_task("test_1", "测试任务")
    add_reviewer_task("review_1", "审查任务")
    add_analyzer_task("analyze_1", "分析任务")
    add_custom_task("custom_1", "自定义提示词", "自定义任务")
    
    manager = get_task_manager()
    
    assert len(manager.tasks) == 5
    assert "dev_1" in manager.tasks
    assert "test_1" in manager.tasks
    assert "review_1" in manager.tasks
    assert "analyze_1" in manager.tasks
    assert "custom_1" in manager.tasks
    
    reset_task_manager()


@pytest.mark.asyncio
async def test_task_manager_start_stop():
    """测试任务管理器启动和停止"""
    reset_task_manager()
    manager = get_task_manager()
    
    # 添加任务
    manager.add_task("task_1", "测试提示词")
    
    # 启动
    await manager.start()
    assert manager.is_running is True
    
    # 等待
    await asyncio.sleep(0.5)
    
    # 停止
    await manager.stop()
    assert manager.is_running is False
    
    reset_task_manager()


@pytest.mark.asyncio
async def test_task_manager_status():
    """测试任务管理器状态"""
    reset_task_manager()
    manager = get_task_manager()
    
    # 添加任务
    manager.add_task("task_1", "任务1")
    manager.add_task("task_2", "任务2")
    
    # 获取状态
    status = manager.get_status()
    
    assert status["total_tasks"] == 2
    assert status["running_tasks"] == 0
    assert "task_1" in status["tasks"]
    assert "task_2" in status["tasks"]
    
    reset_task_manager()


@pytest.mark.asyncio
async def test_global_task_manager():
    """测试全局任务管理器"""
    reset_task_manager()
    
    manager1 = get_task_manager()
    manager2 = get_task_manager()
    
    # 应该是同一个实例
    assert manager1 is manager2
    
    # 重置
    reset_task_manager()
    
    # 获取新实例
    manager3 = get_task_manager()
    assert manager3 is not manager1
    
    reset_task_manager()


def test_simple_guardian_init():
    """测试极简守护初始化"""
    guardian = SimpleGuardian(Path.cwd())
    
    assert guardian.is_running is False
    assert guardian.check_interval == 60
    assert len(guardian.monitored_pids) == 0


def test_simple_guardian_register_process():
    """测试守护注册进程"""
    guardian = SimpleGuardian(Path.cwd())
    
    # 注册进程
    guardian.register_process("test_process", 12345)
    
    assert "test_process" in guardian.monitored_pids
    assert guardian.monitored_pids["test_process"] == 12345
    assert guardian.restart_counts["test_process"] == 0


def test_simple_guardian_is_process_alive():
    """测试进程存活检查"""
    guardian = SimpleGuardian(Path.cwd())
    
    # 检查当前进程
    is_alive = guardian._is_process_alive(12345)
    assert is_alive is False
    
    # 检查一个不存在的 PID
    is_alive = guardian._is_process_alive(999999)
    assert is_alive is False


def test_simple_guardian_get_status():
    """测试守护状态"""
    guardian = SimpleGuardian(Path.cwd())
    
    # 注册进程
    guardian.register_process("process1", 12345)
    guardian.register_process("process2", 67890)
    
    # 获取状态
    status = guardian.get_status()
    
    assert status["is_running"] is False
    assert status["check_interval"] == 60
    assert len(status["monitored_processes"]) == 2
    assert "process1" in status["monitored_processes"]
    assert "process2" in status["monitored_processes"]


@pytest.mark.asyncio
async def test_simple_guardian_start_stop():
    """测试守护启动和停止"""
    guardian = SimpleGuardian(Path.cwd(), check_interval=1)
    
    # 注册进程
    guardian.register_process("test_process", 12345)
    
    # 启动
    await guardian.start()
    assert guardian.is_running is True
    
    # 等待
    await asyncio.sleep(2)
    
    # 停止
    await guardian.stop()
    assert guardian.is_running is False


def test_create_guardian_convenience():
    """测试创建守护便捷函数"""
    guardian = create_guardian()
    
    assert isinstance(guardian, SimpleGuardian)
    assert guardian.is_running is False


def test_prompt_task_dataclass():
    """测试提示词任务数据类"""
    task = PromptTask(
        task_id="test_id",
        prompt="测试提示词",
        description="测试任务"
    )
    
    assert task.task_id == "test_id"
    assert task.prompt == "测试提示词"
    assert task.description == "测试任务"
    assert task.is_running is False
    assert task.pid is None


def test_simple_architecture_integration():
    """测试极简架构集成"""
    reset_task_manager()
    
    # 创建任务管理器
    task_manager = get_task_manager()
    
    # 添加任务
    task_manager.add_task_from_template(
        "task_1",
        "developer",
        "实现功能"
    )
    
    # 创建守护
    guardian = SimpleGuardian(Path.cwd())
    guardian.register_process("ai_loop", 12345)
    
    # 验证
    assert len(task_manager.tasks) == 1
    assert len(guardian.monitored_pids) == 1
    
    reset_task_manager()