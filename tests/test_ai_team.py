"""测试 AI 团队系统

测试多个 AI 循环组成的团队
"""
import pytest
import asyncio
import time
from pathlib import Path

from dev_bot.ai_team import (
    AITeamManager,
    AIRole,
    TaskStatus,
    AITeamMember,
    TeamTask
)
from dev_bot.output_router import get_output_router, reset_output_router


@pytest.mark.asyncio
async def test_ai_team_manager_init():
    """测试 AI 团队管理器初始化"""
    project_root = Path.cwd()
    manager = AITeamManager(project_root, check_interval=5)

    assert manager.project_root == project_root
    assert manager.check_interval == 5
    assert manager.is_running is False
    assert len(manager.members) == 0


@pytest.mark.asyncio
async def test_ai_team_manager_start_stop():
    """测试启动和停止"""
    reset_output_router()
    project_root = Path.cwd()
    manager = AITeamManager(project_root, check_interval=1)

    # 启动团队
    await manager.start()
    assert manager.is_running is True
    assert len(manager.members) > 0

    # 等待一段时间
    await asyncio.sleep(0.5)

    # 停止团队
    await manager.stop()
    assert manager.is_running is False

    reset_output_router()


@pytest.mark.asyncio
async def test_ai_team_get_status():
    """测试获取状态"""
    reset_output_router()
    project_root = Path.cwd()
    manager = AITeamManager(project_root)

    # 启动团队
    await manager.start()

    # 获取状态
    status = await manager.get_status()

    assert "is_running" in status
    assert "team_name" in status
    assert "members" in status
    assert "tasks" in status

    # 停止团队
    await manager.stop()
    reset_output_router()


@pytest.mark.asyncio
async def test_add_task():
    """测试添加任务"""
    reset_output_router()
    project_root = Path.cwd()
    manager = AITeamManager(project_root, check_interval=1)

    # 启动团队
    await manager.start()

    # 添加任务
    task_id = await manager.add_task(
        "编写测试代码",
        AIRole.DEVELOPER
    )

    assert task_id.startswith("task_")
    assert len(manager.task_queue) > 0

    # 停止团队
    await manager.stop()
    reset_output_router()


@pytest.mark.asyncio
async def test_complete_task():
    """测试完成任务"""
    reset_output_router()
    project_root = Path.cwd()
    manager = AITeamManager(project_root)

    # 启动团队
    await manager.start()

    # 添加任务
    task_id = await manager.add_task("测试任务", AIRole.TESTER)

    # 等待任务分配
    await asyncio.sleep(2)

    # 完成任务
    result = {"output": "测试通过"}
    await manager.complete_task(task_id, result, success=True)

    # 检查统计
    assert manager.completed_tasks_count > 0

    # 停止团队
    await manager.stop()
    reset_output_router()


@pytest.mark.asyncio
async def test_ai_team_member_creation():
    """测试团队成员创建"""
    member = AITeamMember(
        member_id="developer_1",
        role=AIRole.DEVELOPER
    )

    assert member.member_id == "developer_1"
    assert member.role == AIRole.DEVELOPER
    assert member.is_healthy is True
    assert member.tasks_completed == 0
    assert member.tasks_failed == 0


def test_ai_team_member_to_dict():
    """测试团队成员转换为字典"""
    member = AITeamMember(
        member_id="tester_1",
        role=AIRole.TESTER
    )

    data = member.to_dict()

    assert data["member_id"] == "tester_1"
    assert data["role"] == "tester"
    assert data["is_healthy"] is True
    assert data["tasks_completed"] == 0


def test_team_task_creation():
    """测试团队任务创建"""
    task = TeamTask(
        task_id="task_1",
        description="审查代码",
        required_role=AIRole.REVIEWER
    )

    assert task.task_id == "task_1"
    assert task.description == "审查代码"
    assert task.required_role == AIRole.REVIEWER
    assert task.status == TaskStatus.PENDING
    assert task.assigned_to is None


def test_team_task_to_dict():
    """测试团队任务转换为字典"""
    task = TeamTask(
        task_id="task_1",
        description="分析需求",
        required_role=AIRole.ANALYZER
    )

    data = task.to_dict()

    assert data["task_id"] == "task_1"
    assert data["description"] == "分析需求"
    assert data["required_role"] == "analyzer"
    assert data["status"] == "pending"


def test_ai_role_enum():
    """测试 AI 角色枚举"""
    assert AIRole.DEVELOPER.value == "developer"
    assert AIRole.TESTER.value == "tester"
    assert AIRole.REVIEWER.value == "reviewer"
    assert AIRole.ANALYZER.value == "analyzer"
    assert AIRole.OPTIMIZER.value == "optimizer"
    assert AIRole.DOCUMENTER.value == "documenter"


def test_task_status_enum():
    """测试任务状态枚举"""
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.ASSIGNED.value == "assigned"
    assert TaskStatus.IN_PROGRESS.value == "in_progress"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"


@pytest.mark.asyncio
async def test_team_collaboration():
    """测试团队协作"""
    reset_output_router()
    project_root = Path.cwd()
    manager = AITeamManager(project_root, check_interval=1)

    # 启动团队
    await manager.start()

    # 添加多个任务
    await manager.add_task("编写功能代码", AIRole.DEVELOPER)
    await manager.add_task("编写测试用例", AIRole.TESTER)
    await manager.add_task("代码审查", AIRole.REVIEWER)

    # 等待任务分发
    await asyncio.sleep(3)

    # 检查状态
    status = await manager.get_status()
    assert status["tasks"]["total"] >= 3

    # 停止团队
    await manager.stop()
    reset_output_router()


@pytest.mark.asyncio
async def test_member_health_check():
    """测试成员健康检查"""
    reset_output_router()
    project_root = Path.cwd()
    manager = AITeamManager(project_root, check_interval=0.5)

    # 启动团队
    await manager.start()

    # 等待成员启动
    await asyncio.sleep(2)

    # 检查所有成员
    await manager._check_all_members()

    # 验证成员健康状态
    for member in manager.members.values():
        assert member.is_healthy is not None

    # 停止团队
    await manager.stop()
    reset_output_router()


def test_import_ai_team():
    """测试导入"""
    from dev_bot.ai_team import AITeamManager, AIRole, TaskStatus
    assert AITeamManager is not None
    assert AIRole is not None
    assert TaskStatus is not None