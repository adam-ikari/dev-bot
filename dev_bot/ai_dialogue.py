"""AI 对话机制

极简设计 + 完全自主的 AI 对话
"""
import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set

from dev_bot.core import get_core
from dev_bot.output_router import get_output_router, OutputSource, LogLevel


class DialogueMode(Enum):
    """对话模式"""
    ONE_TO_ONE = "one_to_one"
    GROUP = "group"


@dataclass
class AIRole:
    """AI 角色"""
    role_id: str
    name: str
    prompt: str
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.role_id or not self.role_id.strip():
            raise ValueError("role_id cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("name cannot be empty")
        if not self.prompt or not self.prompt.strip():
            raise ValueError("prompt cannot be empty")


@dataclass
class Message:
    """消息"""
    sender_id: str
    content: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "sender_id": self.sender_id,
            "content": self.content,
            "timestamp": self.timestamp
        }


@dataclass
class Dialogue:
    """对话"""
    dialogue_id: str
    mode: DialogueMode
    participants: List[str]
    topic: str
    messages: deque = field(default_factory=lambda: deque(maxlen=1000))
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    
    def add_message(self, message: Message) -> None:
        """添加消息"""
        self.messages.append(message)
        self.last_activity = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "dialogue_id": self.dialogue_id,
            "mode": self.mode.value,
            "participants": self.participants,
            "topic": self.topic,
            "message_count": len(self.messages),
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "recent_messages": [m.to_dict() for m in list(self.messages)[-10:]]
        }


class AutonomousDialogueManager:
    """自主对话管理器
    
    极简设计 + 完全自主的 AI 对话
    - 不需要固定流程
    - AI 自主决定何时发言
    - AI 自主决定何时结束
    """
    
    def __init__(
        self,
        iflow_timeout: int = 60,
        consensus_timeout: int = 30,
        summary_timeout: int = 60,
        max_idle_time: int = 300
    ):
        self.core = get_core()
        self.output_router = get_output_router()
        
        # 超时配置
        self.iflow_timeout = iflow_timeout
        self.consensus_timeout = consensus_timeout
        self.summary_timeout = summary_timeout
        self.max_idle_time = max_idle_time
        
        # 角色和对话
        self.roles: Dict[str, AIRole] = {}
        self.dialogues: Dict[str, Dialogue] = {}
        
        # 初始化默认角色
        self._init_default_roles()
    
    def _init_default_roles(self) -> None:
        """初始化默认角色"""
        default_roles = [
            AIRole(
                role_id="developer",
                name="开发者",
                prompt="""你是一个开发者，负责编写代码和实现功能。
在对话中，你应该：
1. 从技术角度分析问题
2. 提供实现方案
3. 讨论技术细节
4. 给出代码示例

自主发言规则：
- 只在有技术见解时发言
- 不要重复相同的观点
- 对其他人的技术观点可以回应或补充"""
            ),
            AIRole(
                role_id="tester",
                name="测试者",
                prompt="""你是一个测试者，负责编写测试用例和执行测试。
在对话中，你应该：
1. 提出测试需求
2. 设计测试方案
3. 指出潜在问题
4. 确保质量

自主发言规则：
- 只在有测试相关见解时发言
- 指出测试覆盖和边界情况
- 不要重复已提出的测试点"""
            ),
            AIRole(
                role_id="reviewer",
                name="审查者",
                prompt="""你是一个审查者，负责审查代码质量和安全性。
在对话中，你应该：
1. 检查代码规范
2. 分析安全性
3. 评估质量
4. 提供改进建议

自主发言规则：
- 只在有质量或安全见解时发言
- 指出代码规范和最佳实践
- 不要重复已指出的安全问题"""
            ),
            AIRole(
                role_id="analyzer",
                name="分析师",
                prompt="""你是一个分析师，负责分析需求和设计方案。
在对话中，你应该：
1. 理解需求
2. 分析可行性
3. 设计方案
4. 提供建议

自主发言规则：
- 只在有分析见解时发言
- 提供需求澄清和可行性分析
- 不要重复已提出的分析观点"""
            ),
            AIRole(
                role_id="moderator",
                name="主持人",
                prompt="""你是对话主持人，负责引导对话进程。
在对话中，你应该：
1. 引导讨论方向
2. 总结关键点
3. 促进共识
4. 控制节奏

自主发言规则：
- 只在需要引导或总结时发言
- 不要打断有价值的讨论
- 在对话陷入僵局时介入"""
            )
        ]
        
        for role in default_roles:
            self.roles[role.role_id] = role
    
    def add_role(self, role_id: str, name: str, prompt: str) -> None:
        """添加角色
        
        Args:
            role_id: 角色 ID
            name: 角色名称
            prompt: 角色提示词
        
        Raises:
            ValueError: 如果输入无效或角色已存在
        """
        if not role_id or not role_id.strip():
            raise ValueError("role_id cannot be empty")
        if not name or not name.strip():
            raise ValueError("name cannot be empty")
        if not prompt or not prompt.strip():
            raise ValueError("prompt cannot be empty")
        if role_id in self.roles:
            raise ValueError(f"Role {role_id} already exists")
        
        role = AIRole(role_id=role_id, name=name, prompt=prompt)
        self.roles[role_id] = role
    
    def create_dialogue(
        self,
        participants: List[str],
        topic: str,
        mode: DialogueMode = DialogueMode.GROUP
    ) -> str:
        """创建对话
        
        Args:
            participants: 参与者角色 ID 列表
            topic: 对话主题
            mode: 对话模式
        
        Returns:
            对话 ID
        
        Raises:
            ValueError: 如果参与者无效或主题为空
        """
        if not participants:
            raise ValueError("participants cannot be empty")
        if not topic or not topic.strip():
            raise ValueError("topic cannot be empty")
        
        # 验证参与者
        for participant_id in participants:
            if participant_id not in self.roles:
                raise ValueError(f"Unknown role: {participant_id}")
        
        dialogue_id = f"dialogue_{int(time.time())}_{len(self.dialogues)}"
        
        dialogue = Dialogue(
            dialogue_id=dialogue_id,
            mode=mode,
            participants=participants.copy(),
            topic=topic
        )
        
        self.dialogues[dialogue_id] = dialogue
        
        return dialogue_id
        
    
    async def start_autonomous_dialogue(
        self,
        dialogue_id: str,
        max_duration: int = 600
    ) -> None:
        """开始自主对话
        
        Args:
            dialogue_id: 对话 ID
            max_duration: 最大持续时间（秒）
        """
        if dialogue_id not in self.dialogues:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                f"Dialogue not found: {dialogue_id}"
            )
            return
        
        dialogue = self.dialogues[dialogue_id]
        
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"Starting autonomous dialogue: {dialogue_id}"
        )
        
        try:
            # 发起对话
            await self._initiate_dialogue(dialogue)
            
            # 自主对话循环
            start_time = time.time()
            
            while dialogue.is_active and (time.time() - start_time) < max_duration:
                # 检查是否空闲太久
                if time.time() - dialogue.last_activity > self.max_idle_time:
                    await self.output_router.emit(
                        OutputSource.SYSTEM,
                        LogLevel.INFO,
                        f"Dialogue idle timeout: {dialogue_id}"
                    )
                    break
                
                # 让 AI 自主决定是否发言
                spoke = await self._autonomous_round(dialogue)
                
                # 如果没有人发言，尝试结束对话
                if not spoke:
                    should_end = await self._should_end_dialogue(dialogue)
                    if should_end:
                        await self.output_router.emit(
                            OutputSource.SYSTEM,
                            LogLevel.INFO,
                            f"Dialogue reached consensus: {dialogue_id}"
                        )
                        break
                
                # 短暂休息
                await asyncio.sleep(1)
            
            # 总结对话
            await self._summarize_dialogue(dialogue)
        
        except Exception as e:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                f"Dialogue error: {dialogue_id} - {str(e)}"
            )
            raise
        
        finally:
            dialogue.is_active = False
            
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.INFO,
                f"Dialogue ended: {dialogue_id}"
            )
    
    async def _initiate_dialogue(self, dialogue: Dialogue) -> None:
        """发起对话
        
        Args:
            dialogue: 对话对象
        """
        # 使用第一个参与者发起对话
        first_participant = dialogue.participants[0]
        role = self.roles[first_participant]
        
        prompt = f"""你是 {role.name}。

角色定义：
{role.prompt}

对话主题：
{dialogue.topic}

请发起对话，开始讨论这个主题。
"""
        
        try:
            result = await self.core.call_iflow(prompt, timeout=self.iflow_timeout)
            
            if result["success"]:
                message = Message(
                    sender_id=first_participant,
                    content=result["output"]
                )
                dialogue.add_message(message)
                
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.INFO,
                    f"[{role.name}]: {result['output'][:200]}..."
                )
            else:
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.ERROR,
                    f"Failed to initiate dialogue: {result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                f"Exception initiating dialogue: {str(e)}"
            )
            raise
    
    async def _autonomous_round(self, dialogue: Dialogue) -> bool:
        """自主对话轮次
        
        Args:
            dialogue: 对话对象
        
        Returns:
            是否有人发言
        """
        # 获取最近的对话历史
        recent_messages = list(dialogue.messages)[-5:]
        
        # 构建对话历史
        history = "\n".join([
            f"[{self.roles[m.sender_id].name}]: {m.content}"
            for m in recent_messages
        ]) if recent_messages else "（对话尚未开始）"
        
        # 构建参与者列表
        participants_info = "\n".join([
            f"{idx}. {self.roles[pid].name} ({pid})"
            for idx, pid in enumerate(dialogue.participants)
        ])
        
        # 让 AI 决定是否需要继续对话，以及谁应该发言
        prompt = f"""你是对话协调者。

对话主题：
{dialogue.topic}

参与者：
{participants_info}

最近的对话：
{history}

判断：
1. 对话是否需要继续？
2. 如果需要，谁应该发言？（只回答参与者的编号或角色ID）
3. 如果不需要，返回 "END"

只回答：
- 需要发言时，返回角色ID
- 不需要发言时，返回 "END"
- 保持对话自然流畅"""
        
        try:
            result = await self.core.call_iflow(
                prompt,
                timeout=self.consensus_timeout
            )
            
            if result["success"]:
                response = result["output"].strip()
                
                # 检查是否需要结束
                if "END" in response.upper():
                    return False
                
                # 解析角色ID
                next_speaker = response.strip()
                
                # 查找对应的角色ID
                speaker_id = None
                for pid in dialogue.participants:
                    if pid == next_speaker or self.roles[pid].name == next_speaker:
                        speaker_id = pid
                        break
                
                if speaker_id:
                    try:
                        await self._participant_speak(
                            dialogue,
                            speaker_id,
                            history
                        )
                        return True
                    except Exception as e:
                        await self.output_router.emit(
                            OutputSource.SYSTEM,
                            LogLevel.ERROR,
                            f"Error while {speaker_id} speaking: {str(e)}"
                        )
                        return False
        
        except Exception as e:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                f"Error in autonomous round: {str(e)}"
            )
        
        return False
    
    async def _should_speak(
        self,
        dialogue: Dialogue,
        participant_id: str,
        history: str
    ) -> bool:
        """判断参与者是否应该发言
        
        Args:
            dialogue: 对话对象
            participant_id: 参与者 ID
            history: 对话历史
        
        Returns:
            是否应该发言
        """
        role = self.roles[participant_id]
        
        prompt = f"""你是 {role.name}。

角色定义：
{role.prompt}

对话主题：
{dialogue.topic}

最近的对话：
{history}

判断：你现在应该发言吗？

只回答 YES 或 NO。
- 只有在有你独特的见解需要分享时才回答 YES
- 如果你的观点已经被表达过，或者你没有什么新内容，回答 NO"""
        
        try:
            result = await self.core.call_iflow(
                prompt,
                timeout=self.consensus_timeout
            )
            
            if result["success"]:
                response = result["output"].upper()
                return "YES" in response
        
        except Exception:
            pass
        
        return False
    
    async def _participant_speak(
        self,
        dialogue: Dialogue,
        participant_id: str,
        history: str
    ) -> None:
        """参与者发言
        
        Args:
            dialogue: 对话对象
            participant_id: 参与者 ID
            history: 对话历史
        """
        role = self.roles[participant_id]
        
        # 获取最近的对话历史
        recent_messages = list(dialogue.messages)[-5:]
        
        history = "\n".join([
            f"[{self.roles[m.sender_id].name}]: {m.content}"
            for m in recent_messages
        ]) if recent_messages else "（对话尚未开始）"
        
        prompt = f"""你是 {role.name}。

角色定义：
{role.prompt}

对话主题：
{dialogue.topic}

最近的对话：
{history}

请根据你的角色和对话上下文，参与讨论。
保持简明扼要，不要重复已有的观点。"""
        
        try:
            result = await self.core.call_iflow(prompt, timeout=self.iflow_timeout)
            
            if result["success"]:
                message = Message(
                    sender_id=participant_id,
                    content=result["output"]
                )
                dialogue.add_message(message)
                
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.INFO,
                    f"[{role.name}]: {result['output'][:200]}..."
                )
            else:
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.ERROR,
                    f"Failed to get response from {role.name}: {result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                f"Exception while {role.name} speaking: {str(e)}"
            )
            raise
    
    async def _should_end_dialogue(self, dialogue: Dialogue) -> bool:
        """判断是否应该结束对话
        
        Args:
            dialogue: 对话对象
        
        Returns:
            是否应该结束
        """
        # 获取最近的对话历史
        recent_messages = list(dialogue.messages)[-3:]
        
        if not recent_messages:
            return False
        
        history = "\n".join([
            f"[{self.roles[m.sender_id].name}]: {m.content}"
            for m in recent_messages
        ])
        
        prompt = f"""判断以下对话是否达成共识，可以结束讨论。

对话主题：
{dialogue.topic}

最近的对话：
{history}

请回答：
- 如果达成共识或对话已充分展开，返回 "YES"
- 如果还有重要问题未讨论，返回 "NO"
- 简要说明原因"""
        
        try:
            result = await self.core.call_iflow(
                prompt,
                timeout=self.consensus_timeout
            )
            
            if result["success"]:
                response = result["output"].upper()
                return "YES" in response
        except Exception:
            pass
        
        return False
    
    async def _summarize_dialogue(self, dialogue: Dialogue) -> None:
        """总结对话
        
        Args:
            dialogue: 对话对象
        """
        # 构建完整对话历史
        history = "\n".join([
            f"[{self.roles[m.sender_id].name}]: {m.content}"
            for m in dialogue.messages
        ])
        
        if not history:
            return
        
        prompt = f"""请总结以下对话。

对话主题：
{dialogue.topic}

参与者：
{', '.join([self.roles[p].name for p in dialogue.participants])}

对话内容：
{history}

请提供：
1. 主要观点
2. 达成的共识
3. 未解决的问题
4. 下一步建议"""
        
        try:
            result = await self.core.call_iflow(prompt, timeout=self.summary_timeout)
            
            if result["success"]:
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.SUCCESS,
                    f"Dialogue summary:\n{result['output']}"
                )
            else:
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.ERROR,
                    f"Failed to summarize dialogue: {result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.ERROR,
                f"Exception summarizing dialogue: {str(e)}"
            )
    
    def get_dialogue(self, dialogue_id: str) -> Optional[Dialogue]:
        """获取对话
        
        Args:
            dialogue_id: 对话 ID
        
        Returns:
            对话对象
        """
        return self.dialogues.get(dialogue_id)
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态
        
        Returns:
            状态字典
        """
        return {
            "total_roles": len(self.roles),
            "total_dialogues": len(self.dialogues),
            "active_dialogues": sum(1 for d in self.dialogues.values() if d.is_active),
            "roles": [role.name for role in self.roles.values()]
        }


# 全局对话管理器实例
_global_dialogue_manager: Optional[AutonomousDialogueManager] = None


def get_dialogue_manager() -> AutonomousDialogueManager:
    """获取全局对话管理器实例
    
    Returns:
        对话管理器实例
    """
    global _global_dialogue_manager
    
    if _global_dialogue_manager is None:
        _global_dialogue_manager = AutonomousDialogueManager()
    
    return _global_dialogue_manager


def reset_dialogue_manager() -> None:
    """重置全局对话管理器"""
    global _global_dialogue_manager
    _global_dialogue_manager = None


# 便捷函数
def create_developer_tester_dialogue(topic: str) -> str:
    """创建开发者-测试者对话
    
    Args:
        topic: 对话主题
    
    Returns:
        对话 ID
    """
    manager = get_dialogue_manager()
    return manager.create_dialogue(
        participants=["developer", "tester"],
        topic=topic,
        mode=DialogueMode.ONE_TO_ONE
    )


def create_team_dialogue(topic: str) -> str:
    """创建团队对话（多 AI 讨论）
    
    Args:
        topic: 对话主题
    
    Returns:
        对话 ID
    """
    manager = get_dialogue_manager()
    return manager.create_dialogue(
        participants=["analyzer", "developer", "tester", "reviewer"],
        topic=topic,
        mode=DialogueMode.GROUP
    )
