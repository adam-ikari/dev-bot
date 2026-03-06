#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 循环指令调度系统

将 AI 循环重新设计为纯粹的指令调度系统：
- 生成指令
- 管理指令队列
- 调度 iflow 执行
- 跟踪执行状态
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from dev_bot.iflow_manager import get_iflow_manager, IFlowMode


class CommandType(Enum):
    """指令类型"""
    ANALYZE = "analyze"  # 分析
    DEVELOP = "develop"  # 开发
    DEBUG = "debug"  # 调试
    OPTIMIZE = "optimize"  # 优化
    REFACTOR = "refactor"  # 重构
    TEST = "test"  # 测试
    DOCUMENT = "document"  # 文档
    DEPLOY = "deploy"  # 部署
    CUSTOM = "custom"  # 自定义


class CommandStatus(Enum):
    """指令状态"""
    PENDING = "pending"  # 等待中
    QUEUED = "queued"  # 已排队
    EXECUTING = "executing"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class CommandPriority(Enum):
    """指令优先级"""
    URGENT = "urgent"  # 紧急
    HIGH = "high"  # 高
    NORMAL = "normal"  # 正常
    LOW = "low"  # 低


@dataclass
class Command:
    """指令"""
    id: str
    type: CommandType
    priority: CommandPriority
    prompt: str
    iflow_mode: IFlowMode = IFlowMode.NORMAL
    context: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 300
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "prompt": self.prompt,
            "iflow_mode": self.iflow_mode.value,
            "context": self.context,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "created_at": self.created_at
        }


@dataclass
class CommandResult:
    """指令执行结果"""
    command_id: str
    status: CommandStatus
    output: str = ""
    error: str = ""
    duration: float = 0.0
    started_at: str = ""
    completed_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "command_id": self.command_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration": self.duration,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }


class CommandQueue:
    """指令队列
    
    管理指令的排队和调度
    """
    
    def __init__(self):
        self.queue: List[Command] = []
        self.completed: Dict[str, CommandResult] = {}
        self.failed: Dict[str, CommandResult] = {}
        self.current_index = 0
        
        print(f"[指令队列] 初始化完成")
    
    def add_command(self, command: Command):
        """添加指令到队列"""
        # 按优先级插入
        insert_index = len(self.queue)
        for i, cmd in enumerate(self.queue):
            if self._compare_priority(command.priority, cmd.priority) > 0:
                insert_index = i
                break
        
        self.queue.insert(insert_index, command)
        print(f"[指令队列] 添加指令: {command.id} (类型: {command.type.value}, 优先级: {command.priority.value})")
    
    def _compare_priority(self, p1: CommandPriority, p2: CommandPriority) -> int:
        """比较优先级"""
        priority_order = {
            CommandPriority.URGENT: 4,
            CommandPriority.HIGH: 3,
            CommandPriority.NORMAL: 2,
            CommandPriority.LOW: 1
        }
        return priority_order[p1] - priority_order[p2]
    
    def get_next_command(self) -> Optional[Command]:
        """获取下一个待执行的指令"""
        while self.current_index < len(self.queue):
            command = self.queue[self.current_index]
            
            # 检查依赖
            if self._check_dependencies(command):
                self.current_index += 1
                return command
            else:
                self.current_index += 1
        
        return None
    
    def _check_dependencies(self, command: Command) -> bool:
        """检查依赖是否满足"""
        for dep_id in command.dependencies:
            if dep_id not in self.completed:
                return False
        return True
    
    def mark_completed(self, command_id: str, result: CommandResult):
        """标记指令完成"""
        self.completed[command_id] = result
        print(f"[指令队列] 指令完成: {command_id}")
    
    def mark_failed(self, command_id: str, result: CommandResult):
        """标记指令失败"""
        self.failed[command_id] = result
        print(f"[指令队列] 指令失败: {command_id}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "queue_length": len(self.queue),
            "current_index": self.current_index,
            "pending": len(self.queue) - self.current_index,
            "completed": len(self.completed),
            "failed": len(self.failed)
        }
    
    def get_pending_commands(self) -> List[Command]:
        """获取待执行的指令"""
        return self.queue[self.current_index:]
    
    def clear_completed(self):
        """清理已完成的指令"""
        if self.current_index > 0:
            self.queue = self.queue[self.current_index:]
            self.current_index = 0
            print(f"[指令队列] 清理已完成的指令")


class CommandDispatcher:
    """指令调度器
    
    负责调度 iflow 执行指令
    """
    
    def __init__(self, iflow_command: str = "iflow"):
        self.iflow_command = iflow_command
        self.iflow_manager = get_iflow_manager(iflow_command)
        self.active_commands: Dict[str, asyncio.Task] = {}
        self.command_queue = CommandQueue()
        
        print(f"[指令调度器] 初始化完成")
    
    async def dispatch(self, command: Command) -> CommandResult:
        """调度执行指令"""
        result = CommandResult(
            command_id=command.id,
            status=CommandStatus.EXECUTING,
            started_at=datetime.now().isoformat()
        )
        
        try:
            print(f"[指令调度器] 执行指令: {command.id}")
            print(f"[指令调度器] 类型: {command.type.value}, 模式: {command.iflow_mode.value}")
            
            # 调用 iflow
            iflow_result = await self.iflow_manager.call(
                prompt=command.prompt,
                mode=command.iflow_mode,
                timeout=command.timeout,
                context=command.context
            )
            
            result.output = iflow_result.output
            result.error = iflow_result.error
            result.duration = iflow_result.duration
            result.status = CommandStatus.COMPLETED if iflow_result.success else CommandStatus.FAILED
            result.completed_at = datetime.now().isoformat()
            
            if iflow_result.success:
                self.command_queue.mark_completed(command.id, result)
                print(f"[指令调度器] 指令完成: {command.id} (耗时: {result.duration:.2f}秒)")
            else:
                self.command_queue.mark_failed(command.id, result)
                print(f"[指令调度器] 指令失败: {command.id}")
            
        except Exception as e:
            result.status = CommandStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now().isoformat()
            self.command_queue.mark_failed(command.id, result)
            print(f"[指令调度器] 指令异常: {command.id} - {e}")
        
        return result
    
    async def dispatch_queue(self, max_concurrent: int = 1):
        """调度执行队列中的指令
        
        Args:
            max_concurrent: 最大并发数
        """
        print(f"[指令调度器] 开始调度队列（最大并发: {max_concurrent}）")
        
        queue_status = self.command_queue.get_queue_status()
        print(f"[指令调度器] 队列状态: {queue_status}")
        
        # 执行队列中的指令
        active_tasks = []
        
        while True:
            # 获取下一个指令
            command = self.command_queue.get_next_command()
            
            if command is None:
                break
            
            # 等待并发数限制
            while len(active_tasks) >= max_concurrent:
                done, pending = await asyncio.wait(active_tasks, return_when=asyncio.FIRST_COMPLETED)
                active_tasks = pending
            
            # 执行指令
            task = asyncio.create_task(self.dispatch(command))
            active_tasks.append(task)
        
        # 等待所有任务完成
        if active_tasks:
            await asyncio.wait(active_tasks)
        
        print(f"[指令调度器] 队列调度完成")


class CommandScheduler:
    """指令调度系统
    
    整合指令生成、队列管理和调度执行
    """
    
    def __init__(self, project_root: Path, iflow_command: str = "iflow"):
        self.project_root = project_root
        self.iflow_command = iflow_command
        
        self.dispatcher = CommandDispatcher(iflow_command)
        self.command_generators: Dict[CommandType, Callable] = {}
        
        # 注册默认指令生成器
        self._register_default_generators()
        
        print(f"[指令调度系统] 初始化完成")
    
    def _register_default_generators(self):
        """注册默认指令生成器"""
        
        # 分析指令生成器
        def generate_analyze(context: Dict) -> Command:
            return Command(
                id=f"analyze_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=CommandType.ANALYZE,
                priority=CommandPriority.NORMAL,
                prompt="分析当前项目状态，包括代码质量、测试覆盖率、潜在问题等",
                iflow_mode=IFlowMode.PLAN,
                context=context,
                timeout=300
            )
        
        self.command_generators[CommandType.ANALYZE] = generate_analyze
        
        # 开发指令生成器
        def generate_develop(context: Dict) -> Command:
            task = context.get("task", "开发新功能")
            return Command(
                id=f"develop_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=CommandType.DEVELOP,
                priority=CommandPriority.HIGH,
                prompt=f"执行开发任务: {task}",
                iflow_mode=IFlowMode.YOLO,
                context=context,
                timeout=600
            )
        
        self.command_generators[CommandType.DEVELOP] = generate_develop
        
        # 调试指令生成器
        def generate_debug(context: Dict) -> Command:
            error = context.get("error", "未知错误")
            return Command(
                id=f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=CommandType.DEBUG,
                priority=CommandPriority.URGENT,
                prompt=f"调试并修复错误: {error}",
                iflow_mode=IFlowMode.YOLO,
                context=context,
                timeout=600
            )
        
        self.command_generators[CommandType.DEBUG] = generate_debug
        
        # 测试指令生成器
        def generate_test(context: Dict) -> Command:
            return Command(
                id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=CommandType.TEST,
                priority=CommandPriority.HIGH,
                prompt="运行测试并生成测试报告",
                iflow_mode=IFlowMode.YOLO,
                context=context,
                timeout=300
            )
        
        self.command_generators[CommandType.TEST] = generate_test
    
    def register_generator(
        self,
        command_type: CommandType,
        generator: Callable[[Dict], Command]
    ):
        """注册指令生成器"""
        self.command_generators[command_type] = generator
        print(f"[指令调度系统] 注册指令生成器: {command_type.value}")
    
    def generate_command(
        self,
        command_type: CommandType,
        context: Dict[str, Any]
    ) -> Optional[Command]:
        """生成指令"""
        generator = self.command_generators.get(command_type)
        
        if generator:
            command = generator(context)
            self.dispatcher.command_queue.add_command(command)
            return command
        
        print(f"[指令调度系统] 未找到指令生成器: {command_type.value}")
        return None
    
    def add_command(self, command: Command):
        """直接添加指令"""
        self.dispatcher.command_queue.add_command(command)
    
    async def execute_queue(self, max_concurrent: int = 1):
        """执行队列中的所有指令"""
        await self.dispatcher.dispatch_queue(max_concurrent)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return self.dispatcher.command_queue.get_queue_status()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        queue_status = self.dispatcher.command_queue.get_queue_status()
        iflow_stats = self.dispatcher.iflow_manager.get_statistics()
        
        return {
            "queue": queue_status,
            "iflow": iflow_stats,
            "generators_count": len(self.command_generators)
        }


# 全局指令调度系统实例
_global_command_scheduler = None


def get_command_scheduler(
    project_root: Path,
    iflow_command: str = "iflow"
) -> CommandScheduler:
    """获取全局指令调度系统实例"""
    global _global_command_scheduler
    
    if _global_command_scheduler is None:
        _global_command_scheduler = CommandScheduler(project_root, iflow_command)
    
    return _global_command_scheduler


def reset_command_scheduler():
    """重置全局指令调度系统"""
    global _global_command_scheduler
    _global_command_scheduler = None