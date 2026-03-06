"""基于提示词的任务分配系统

极简设计：使用不同的提示词为每个 AI 循环分配任务
"""
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.core import get_core
from dev_bot.ipc import IPCManager
from dev_bot.output_router import get_output_router, OutputSource, LogLevel


@dataclass
class PromptTask:
    """提示词任务"""
    task_id: str
    prompt: str
    description: str
    is_running: bool = False
    pid: Optional[int] = None


class PromptBasedTaskManager:
    """基于提示词的任务管理器
    
    极简设计：使用不同的提示词为每个 AI 循环分配任务
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.core = get_core()
        self.ipc = IPCManager(project_root)
        self.output_router = get_output_router()
        
        self.tasks: Dict[str, PromptTask] = {}
        self.is_running = False
        self._task = None
        
        # 常用提示词模板
        self.prompt_templates = {
            "developer": """
你是一个开发者，负责编写代码和实现功能。
当前任务：{task}

请按照以下步骤完成：
1. 分析需求
2. 设计方案
3. 编写代码
4. 测试验证
            """.strip(),
            
            "tester": """
你是一个测试者，负责编写测试用例和执行测试。
当前任务：{task}

请按照以下步骤完成：
1. 分析测试需求
2. 编写测试用例
3. 执行测试
4. 报告结果
            """.strip(),
            
            "reviewer": """
你是一个审查者，负责审查代码质量和安全性。
当前任务：{task}

请按照以下步骤完成：
1. 检查代码规范
2. 分析安全性
3. 评估质量
4. 提供改进建议
            """.strip(),
            
            "analyzer": """
你是一个分析师，负责分析需求和设计方案。
当前任务：{task}

请按照以下步骤完成：
1. 理解需求
2. 分析可行性
3. 设计方案
4. 提供建议
            """.strip(),
        }
    
    def add_task(self, task_id: str, prompt: str, description: str = "") -> str:
        """添加任务
        
        Args:
            task_id: 任务 ID
            prompt: 提示词
            description: 任务描述
        
        Returns:
            任务 ID
        """
        task = PromptTask(
            task_id=task_id,
            prompt=prompt,
            description=description or prompt
        )
        
        self.tasks[task_id] = task
        
        print(f"[任务管理器] 添加任务: {task_id}")
        print(f"  描述: {description}")
        print(f"  提示词: {prompt[:100]}...")
        
        return task_id
    
    def add_task_from_template(
        self,
        task_id: str,
        role: str,
        task: str
    ) -> str:
        """从模板添加任务
        
        Args:
            task_id: 任务 ID
            role: 角色（developer/tester/reviewer/analyzer）
            task: 任务内容
        
        Returns:
            任务 ID
        """
        if role not in self.prompt_templates:
            raise ValueError(f"未知的角色: {role}")
        
        template = self.prompt_templates[role]
        prompt = template.format(task=task)
        
        return self.add_task(task_id, prompt, f"{role}: {task}")
    
    async def start(self):
        """启动任务管理器"""
        if self.is_running:
            print("[任务管理器] 已在运行")
            return
        
        self.is_running = True
        print("[任务管理器] 启动任务管理器")
        
        # 启动任务执行循环
        self._task = asyncio.create_task(self._execute_tasks())
    
    async def stop(self):
        """停止任务管理器"""
        if not self.is_running:
            return
        
        self.is_running = False
        print("[任务管理器] 停止任务管理器")
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _execute_tasks(self):
        """执行任务循环"""
        while self.is_running:
            for task_id, task in self.tasks.items():
                if not task.is_running:
                    await self._execute_task(task)
            
            await asyncio.sleep(5)
    
    async def _execute_task(self, task: PromptTask):
        """执行单个任务
        
        Args:
            task: 任务对象
        """
        task.is_running = True
        
        print(f"[任务管理器] 执行任务: {task.task_id}")
        
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"开始执行任务: {task.task_id}"
        )
        
        try:
            # 使用 iflow 执行任务
            result = await self.core.call_iflow(task.prompt)
            
            if result["success"]:
                print(f"[任务管理器] 任务成功: {task.task_id}")
                print(f"  耗时: {result['duration']:.2f}秒")
                
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.SUCCESS,
                    f"任务成功: {task.task_id}（耗时: {result['duration']:.2f}秒）"
                )
            else:
                print(f"[任务管理器] 任务失败: {task.task_id}")
                print(f"  错误: {result['error']}")
                
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.ERROR,
                    f"任务失败: {task.task_id} - {result['error']}"
                )
        
        except Exception as e:
            print(f"[任务管理器] 任务出错: {task.task_id} - {e}")
            
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                f"任务出错: {task.task_id} - {e}"
            )
        
        finally:
            task.is_running = False
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "is_running": self.is_running,
            "total_tasks": len(self.tasks),
            "running_tasks": sum(1 for t in self.tasks.values() if t.is_running),
            "tasks": {
                task_id: {
                    "description": task.description,
                    "is_running": task.is_running,
                    "pid": task.pid
                }
                for task_id, task in self.tasks.items()
            }
        }


# 全局任务管理器实例
_global_task_manager = None


def get_task_manager(project_root: Optional[Path] = None) -> PromptBasedTaskManager:
    """获取全局任务管理器实例"""
    global _global_task_manager
    
    if _global_task_manager is None:
        if project_root is None:
            project_root = Path.cwd()
        
        _global_task_manager = PromptBasedTaskManager(project_root)
    
    return _global_task_manager


def reset_task_manager():
    """重置全局任务管理器"""
    global _global_task_manager
    _global_task_manager = None


# 便捷函数
def add_developer_task(task_id: str, task: str) -> str:
    """添加开发者任务"""
    manager = get_task_manager()
    return manager.add_task_from_template(task_id, "developer", task)


def add_tester_task(task_id: str, task: str) -> str:
    """添加测试者任务"""
    manager = get_task_manager()
    return manager.add_task_from_template(task_id, "tester", task)


def add_reviewer_task(task_id: str, task: str) -> str:
    """添加审查者任务"""
    manager = get_task_manager()
    return manager.add_task_from_template(task_id, "reviewer", task)


def add_analyzer_task(task_id: str, task: str) -> str:
    """添加分析师任务"""
    manager = get_task_manager()
    return manager.add_task_from_template(task_id, "analyzer", task)


def add_custom_task(task_id: str, prompt: str, description: str = "") -> str:
    """添加自定义任务"""
    manager = get_task_manager()
    return manager.add_task(task_id, prompt, description)


if __name__ == "__main__":
    import asyncio
    
    async def demo():
        manager = get_task_manager()
        
        # 添加不同角色的任务
        manager.add_task_from_template(
            "task_1",
            "developer",
            "实现一个简单的计算器功能"
        )
        
        manager.add_task_from_template(
            "task_2",
            "tester",
            "为计算器功能编写测试用例"
        )
        
        manager.add_task_from_template(
            "task_3",
            "reviewer",
            "审查计算器代码"
        )
        
        # 启动任务管理器
        await manager.start()
        
        # 等待一段时间
        await asyncio.sleep(10)
        
        # 获取状态
        status = manager.get_status()
        print(f"\n状态: {status}")
        
        # 停止任务管理器
        await manager.stop()
    
    asyncio.run(demo())
