"""AI 团队系统

实现多个 AI 循环与 AI 守护组成的协作团队
"""
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from collections import deque

from dev_bot.ipc import IPCManager
from dev_bot.output_router import (
    get_output_router,
    OutputSource,
    LogLevel
)


class AIRole(Enum):
    """AI 循环角色"""
    DEVELOPER = "developer"  # 开发者：编写代码
    TESTER = "tester"  # 测试者：测试代码
    REVIEWER = "reviewer"  # 审查者：审查代码
    ANALYZER = "analyzer"  # 分析师：分析需求
    OPTIMIZER = "optimizer"  # 优化者：优化性能
    DOCUMENTER = "documenter"  # 文档者：编写文档


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"  # 待处理
    ASSIGNED = "assigned"  # 已分配
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


@dataclass
class AITeamMember:
    """AI 团队成员"""
    member_id: str
    role: AIRole
    pid: Optional[int] = None
    process: Optional[subprocess.Popen] = None
    is_healthy: bool = True
    last_heartbeat: float = field(default_factory=time.time)
    tasks_completed: int = 0
    tasks_failed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "member_id": self.member_id,
            "role": self.role.value,
            "pid": self.pid,
            "is_healthy": self.is_healthy,
            "last_heartbeat": self.last_heartbeat,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed
        }


@dataclass
class TeamTask:
    """团队任务"""
    task_id: str
    description: str
    required_role: AIRole
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "required_role": self.required_role.value,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "result": self.result,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


class AITeamManager:
    """AI 团队管理器

    管理多个 AI 循环组成的团队
    """

    def __init__(self, project_root: Path, check_interval: int = 10):
        self.project_root = project_root
        self.check_interval = check_interval
        self.ipc = IPCManager(project_root)
        self.output_router = get_output_router()

        self.is_running = False
        self.team_name = "dev-bot-team"

        # 团队成员
        self.members: Dict[str, AITeamMember] = {}

        # 任务队列
        self.task_queue: deque[TeamTask] = deque()
        self.active_tasks: Dict[str, TeamTask] = {}
        self.completed_tasks: List[TeamTask] = []

        # 统计
        self.total_tasks = 0
        self.completed_tasks_count = 0
        self.failed_tasks_count = 0

        # 注册信号处理
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)

    async def start(self):
        """启动 AI 团队"""
        self.is_running = True

        await self.output_router.emit_guardian(
            LogLevel.INFO,
            f"启动 AI 团队（PID: {os.getpid()}）"
        )

        # 初始化团队
        await self._init_team()

        # 启动监控循环
        asyncio.create_task(self._monitor_loop())

        # 启动任务分发
        asyncio.create_task(self._task_dispatcher())

        await self.output_router.emit_guardian(
            LogLevel.SUCCESS,
            f"AI 团队已启动（{len(self.members)} 名成员）"
        )

    async def stop(self):
        """停止 AI 团队"""
        self.is_running = False

        await self.output_router.emit_guardian(
            LogLevel.INFO,
            "停止 AI 团队"
        )

        # 停止所有成员
        for member_id in list(self.members.keys()):
            await self._stop_member(member_id)

        await self.output_router.emit_guardian(
            LogLevel.SUCCESS,
            "AI 团队已停止"
        )

    async def _init_team(self):
        """初始化团队"""
        # 定义团队角色
        roles = [
            AIRole.DEVELOPER,
            AIRole.TESTER,
            AIRole.REVIEWER,
            AIRole.ANALYZER
        ]

        # 为每个角色创建一个成员
        for role in roles:
            member_id = f"{role.value}_1"
            await self._add_member(member_id, role)

        await self.output_router.emit_guardian(
            LogLevel.INFO,
            f"团队初始化完成：{len(self.members)} 名成员"
        )

    async def _add_member(self, member_id: str, role: AIRole):
        """添加团队成员"""
        # 创建启动命令
        startup_command = [
            sys.executable,
            str(self.project_root / "dev_bot" / "ai_loop_process.py"),
            str(self.project_root),
            "config.json",
            "--role",
            role.value
        ]

        await self.output_router.emit_guardian(
            LogLevel.INFO,
            f"添加团队成员: {member_id} ({role.value})"
        )

        try:
            # 启动进程
            process = subprocess.Popen(
                startup_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            # 创建成员
            member = AITeamMember(
                member_id=member_id,
                role=role,
                pid=process.pid,
                process=process
            )

            self.members[member_id] = member

            # 启动输出捕获
            asyncio.create_task(self._capture_member_output(member_id))

            await self.output_router.emit_guardian(
                LogLevel.SUCCESS,
                f"团队成员已启动: {member_id} (PID: {process.pid})"
            )

        except Exception as e:
            await self.output_router.emit_guardian(
                LogLevel.ERROR,
                f"添加团队成员失败: {member_id} - {e}"
            )

    async def _stop_member(self, member_id: str):
        """停止团队成员"""
        if member_id not in self.members:
            return

        member = self.members[member_id]

        await self.output_router.emit_guardian(
            LogLevel.INFO,
            f"停止团队成员: {member_id}"
        )

        try:
            if member.process:
                member.process.terminate()
                try:
                    member.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    member.process.kill()
                    member.process.wait()

            del self.members[member_id]

            await self.output_router.emit_guardian(
                LogLevel.SUCCESS,
                f"团队成员已停止: {member_id}"
            )

        except Exception as e:
            await self.output_router.emit_guardian(
                LogLevel.ERROR,
                f"停止团队成员失败: {member_id} - {e}"
            )

    async def _capture_member_output(self, member_id: str):
        """捕获成员输出"""
        if member_id not in self.members:
            return

        member = self.members[member_id]

        async def read_stream(stream, level: LogLevel):
            while True:
                try:
                    line = stream.readline()
                    if not line:
                        break

                    text = line.decode('utf-8', errors='ignore').strip()
                    if text:
                        await self.output_router.emit_ai_loop(
                            level,
                            f"[{member_id}] {text}"
                        )
                except:
                    break

        # 读取 stdout
        asyncio.create_task(
            read_stream(member.process.stdout, LogLevel.INFO)
        )

        # 读取 stderr
        asyncio.create_task(
            read_stream(member.process.stderr, LogLevel.ERROR)
        )

    async def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            await self._check_all_members()
            await asyncio.sleep(self.check_interval)

    async def _check_all_members(self):
        """检查所有成员健康状态"""
        for member_id, member in self.members.items():
            await self._check_member_health(member_id)

    async def _check_member_health(self, member_id: str):
        """检查成员健康状态"""
        if member_id not in self.members:
            return

        member = self.members[member_id]

        # 检查进程是否存在
        try:
            os.kill(member.pid, 0)
            member.is_healthy = True
        except OSError:
            member.is_healthy = False

            await self.output_router.emit_guardian(
                LogLevel.ERROR,
                f"团队成员 {member_id} (PID: {member.pid}) 已停止"
            )

            # 尝试重启
            if self.is_running:
                await self._restart_member(member_id)

    async def _restart_member(self, member_id: str):
        """重启成员"""
        if member_id not in self.members:
            return

        member = self.members[member_id]

        await self.output_router.emit_guardian(
            LogLevel.WARNING,
            f"尝试重启团队成员: {member_id}"
        )

        # 停止旧进程
        if member.process:
            try:
                member.process.kill()
                member.process.wait(timeout=5)
            except:
                pass

        # 等待
        await asyncio.sleep(2)

        # 重新添加
        await self._add_member(member_id, member.role)

    async def _task_dispatcher(self):
        """任务分发器"""
        while self.is_running:
            # 分配待处理任务
            if self.task_queue:
                await self._assign_tasks()

            await asyncio.sleep(1)

    async def _assign_tasks(self):
        """分配任务"""
        if not self.task_queue:
            return

        task = self.task_queue.popleft()

        # 查找合适的成员
        available_member = self._find_available_member(task.required_role)

        if available_member:
            # 分配任务
            task.status = TaskStatus.ASSIGNED
            task.assigned_to = available_member.member_id
            task.started_at = time.time()

            self.active_tasks[task.task_id] = task

            await self.output_router.emit_guardian(
                LogLevel.INFO,
                f"任务已分配: {task.task_id} -> {available_member.member_id}"
            )

            # 发送任务到成员
            await self._send_task_to_member(available_member.member_id, task)
        else:
            # 没有可用成员，放回队列
            self.task_queue.appendleft(task)

    def _find_available_member(self, role: AIRole) -> Optional[AITeamMember]:
        """查找可用成员"""
        for member in self.members.values():
            if member.role == role and member.is_healthy:
                return member
        return None

    async def _send_task_to_member(self, member_id: str, task: TeamTask):
        """发送任务到成员"""
        # 这里通过 IPC 发送任务
        task_file = self.ipc.ipc_dir / f"task_{member_id}.json"

        try:
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task.to_dict(), f, indent=2)
        except Exception as e:
            await self.output_router.emit_guardian(
                LogLevel.ERROR,
                f"发送任务失败: {e}"
            )

    async def add_task(self, description: str, required_role: AIRole) -> str:
        """添加任务"""
        self.total_tasks += 1
        task_id = f"task_{self.total_tasks}_{int(time.time())}"

        task = TeamTask(
            task_id=task_id,
            description=description,
            required_role=required_role
        )

        self.task_queue.append(task)

        await self.output_router.emit_guardian(
            LogLevel.INFO,
            f"任务已添加: {task_id} ({required_role.value})"
        )

        return task_id

    async def complete_task(self, task_id: str, result: Dict[str, Any], success: bool):
        """完成任务"""
        if task_id not in self.active_tasks:
            return

        task = self.active_tasks[task_id]
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.result = result
        task.completed_at = time.time()

        # 更新成员统计
        if task.assigned_to and task.assigned_to in self.members:
            member = self.members[task.assigned_to]
            if success:
                member.tasks_completed += 1
            else:
                member.tasks_failed += 1

        # 移动到已完成列表
        self.completed_tasks.append(task)
        del self.active_tasks[task_id]

        # 更新统计
        if success:
            self.completed_tasks_count += 1
        else:
            self.failed_tasks_count += 1

        await self.output_router.emit_guardian(
            LogLevel.SUCCESS if success else LogLevel.ERROR,
            f"任务已完成: {task_id} ({'成功' if success else '失败'})"
        )

    def _handle_sigterm(self, signum, frame):
        """处理 SIGTERM 信号"""
        asyncio.create_task(self.stop())

    def _handle_sigint(self, signum, frame):
        """处理 SIGINT 信号"""
        asyncio.create_task(self.stop())

    async def get_status(self) -> Dict[str, Any]:
        """获取团队状态"""
        return {
            "is_running": self.is_running,
            "team_name": self.team_name,
            "members": {
                member_id: member.to_dict()
                for member_id, member in self.members.items()
            },
            "tasks": {
                "total": self.total_tasks,
                "pending": len(self.task_queue),
                "active": len(self.active_tasks),
                "completed": self.completed_tasks_count,
                "failed": self.failed_tasks_count
            }
        }