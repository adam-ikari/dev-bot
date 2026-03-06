"""对话整合层

整合 REPL、问题队列和 AI 对话
"""
import asyncio
import time
from typing import Dict, Optional, Any

from dev_bot.ai_dialogue import (
    AutonomousDialogueManager,
    DialogueMode,
    get_dialogue_manager
)
from dev_bot.queue_manager import QuestionQueue
from dev_bot.core import get_core
from dev_bot.output_router import get_output_router, OutputSource, LogLevel


class DialogueIntegrator:
    """对话整合器
    
    整合 REPL、问题队列和 AI 对话
    """
    
    def __init__(self):
        self.core = get_core()
        self.output_router = get_output_router()
        
        # 获取管理器
        self.dialogue_manager = None
        self.task_manager = None
        
        # 当前对话
        self.current_dialogue_id: Optional[str] = None
        
        # 用户角色
        self.user_role_id = "user"
    
    def _initialize(self) -> None:
        """初始化管理器"""
        if self.dialogue_manager is None:
            self.dialogue_manager = get_dialogue_manager()
        
        if self.task_manager is None:
            self.task_manager = QuestionQueue()
        
        # 添加用户角色
        self._add_user_role()
    
    def _add_user_role(self) -> None:
        """添加用户角色"""
        try:
            self.dialogue_manager.add_role(
                role_id=self.user_role_id,
                name="用户",
                prompt="""你是用户，代表提出问题或需求的人。
在对话中，你应该：
1. 提出问题和需求
2. 回答 AI 的提问
3. 提供背景信息
4. 反馈 AI 的方案"""
            )
            # 角色已添加成功
            pass
        except ValueError:
            # 角色已存在
            pass
    
    async def create_dialogue_from_queue(
        self,
        task_id: str,
        participants: Optional[list[str]] = None
    ) -> Optional[str]:
        """从问题队列创建对话
        
        Args:
            task_id: 任务 ID
            participants: 参与者角色 ID 列表
        
        Returns:
            对话 ID
        """
        self._initialize()
        
        if self.task_manager is None:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                "Task manager not available"
            )
            return None
        
        # 获取任务
        task = self.task_manager._questions.get(task_id)
        if not task:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                f"Task not found: {task_id}"
            )
            return None
        
        # 设置参与者
        if participants is None:
            participants = ["analyzer", "developer", "tester", "reviewer"]
        
        # 包含用户
        participants_with_user = participants.copy()
        if self.user_role_id not in participants_with_user:
            participants_with_user.insert(0, self.user_role_id)
        
        # 创建对话
        dialogue_id = self.dialogue_manager.create_dialogue(
            participants=participants_with_user,
            topic=task.prompt,
            mode=DialogueMode.GROUP
        )
        
        self.current_dialogue_id = dialogue_id
        
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"Dialogue created from task: {task_id}"
        )
        
        return dialogue_id
    
    async def add_user_message(
        self,
        content: str,
        dialogue_id: Optional[str] = None
    ) -> bool:
        """添加用户消息到对话
        
        Args:
            content: 消息内容
            dialogue_id: 对话 ID（可选，默认使用当前对话）
        
        Returns:
            是否成功
        """
        self._initialize()
        
        # 使用指定的对话 ID 或当前对话
        target_dialogue_id = dialogue_id or self.current_dialogue_id
        
        if not target_dialogue_id:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.WARNING,
                "No active dialogue to send message to"
            )
            return False
        
        dialogue = self.dialogue_manager.get_dialogue(target_dialogue_id)
        if not dialogue or not dialogue.is_active:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.WARNING,
                f"No active dialogue: {self.current_dialogue_id}"
            )
            return False
        
        # 用户必须在参与者列表中
        if self.user_role_id not in dialogue.participants:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.WARNING,
                "User is not a participant in the current dialogue"
            )
            return False
        
        # 获取对话历史
        recent_messages = list(dialogue.messages)[-5:]
        history = "\n".join([
            f"[{self.dialogue_manager.roles[m.sender_id].name}]: {m.content}"
            for m in recent_messages
        ]) if recent_messages else "（对话尚未开始）"
        
        # 用户发言提示词
        prompt = f"""你是 {self.dialogue_manager.roles[self.user_role_id].name}。

角色定义：
{self.dialogue_manager.roles[self.user_role_id].prompt}

对话主题：
{dialogue.topic}

最近的对话：
{history}

用户输入：
{content}

请根据角色定义和上下文，发表你的观点。"""
        
        try:
            result = await self.core.call_iflow(prompt, timeout=60)
            
            if result["success"]:
                from dev_bot.ai_dialogue import Message
                
                message = Message(
                    sender_id=self.user_role_id,
                    content=result["output"]
                )
                dialogue.add_message(message)
                
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.INFO,
                    f"[用户]: {result['output'][:200]}..."
                )
                
                return True
            else:
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.ERROR,
                    f"Failed to process user message: {result.get('error', 'Unknown error')}"
                )
                return False
        
        except Exception as e:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                f"Exception processing user message: {str(e)}"
            )
            return False
    
    async def start_dialogue(
        self,
        dialogue_id: Optional[str] = None,
        max_duration: int = 600
    ) -> None:
        """开始对话
        
        Args:
            dialogue_id: 对话 ID，None 表示使用当前对话
            max_duration: 最大持续时间
        """
        self._initialize()
        
        if dialogue_id is None:
            dialogue_id = self.current_dialogue_id
        
        if not dialogue_id:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.WARNING,
                "No dialogue specified"
            )
            return
        
        self.current_dialogue_id = dialogue_id
        
        await self.dialogue_manager.start_autonomous_dialogue(
            dialogue_id,
            max_duration=max_duration
        )
        
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"Dialogue started: {dialogue_id}"
        )
    
    async def list_dialogues(self) -> list:
        """列出所有对话
        
        Returns:
            对话列表
        """
        self._initialize()
        
        return list(self.dialogue_manager.dialogues.values())
    
    async def get_dialogue(self, dialogue_id: str) -> Optional[Any]:
        """获取对话
        
        Args:
            dialogue_id: 对话 ID
        
        Returns:
            对话对象
        """
        self._initialize()
        
        return self.dialogue_manager.get_dialogue(dialogue_id)
    
    async def run_dialogue(
        self,
        dialogue_id: str,
        max_duration: int = 300
    ) -> bool:
        """运行对话
        
        Args:
            dialogue_id: 对话 ID
            max_duration: 最大持续时间（秒）
        
        Returns:
            是否成功
        """
        self._initialize()
        
        dialogue = self.dialogue_manager.get_dialogue(dialogue_id)
        
        if not dialogue:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                f"Dialogue not found: {dialogue_id}"
            )
            return False
        
        if not dialogue.is_active:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.WARNING,
                f"Dialogue is not active: {dialogue_id}"
            )
            return False
        
        self.current_dialogue_id = dialogue_id
        
        try:
            await self.dialogue_manager.start_autonomous_dialogue(
                dialogue_id,
                max_duration=max_duration
            )
            
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.INFO,
                f"Dialogue completed: {dialogue_id}"
            )
            
            return True
        except Exception as e:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                f"Dialogue execution error: {str(e)}"
            )
            return False
    
    async def get_dialogue_status(self) -> Dict[str, Any]:
        """获取对话状态
        
        Returns:
            状态字典
        """
        self._initialize()
        
        status = {
            "current_dialogue_id": self.current_dialogue_id,
            "dialogue_manager_status": self.dialogue_manager.get_status(),
            "task_manager_status": await self.task_manager.get_status()
        }
        
        return status


# 全局对话整合器实例
_global_dialogue_integrator: Optional[DialogueIntegrator] = None


def get_dialogue_integrator() -> DialogueIntegrator:
    """获取全局对话整合器实例
    
    Returns:
        对话整合器实例
    """
    global _global_dialogue_integrator
    
    if _global_dialogue_integrator is None:
        _global_dialogue_integrator = DialogueIntegrator()
    
    return _global_dialogue_integrator


def reset_dialogue_integrator() -> None:
    """重置全局对话整合器"""
    global _global_dialogue_integrator
    _global_dialogue_integrator = None