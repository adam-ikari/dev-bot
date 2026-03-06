"""队列管理器

管理问题队列和输入队列
"""
import asyncio
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class QuestionStatus(Enum):
    """问题状态"""
    PENDING = "pending"  # 等待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class InputStatus(Enum):
    """输入状态"""
    PENDING = "pending"  # 等待输入
    PROVIDED = "provided"  # 已提供
    CONSUMED = "consumed"  # 已消费


@dataclass
class Question:
    """问题数据结构"""
    id: str
    prompt: str
    mode: str = ""  # iflow 模式
    priority: int = 0  # 优先级（0 最高）
    created_at: float = field(default_factory=time.time)
    status: QuestionStatus = QuestionStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "prompt": self.prompt,
            "mode": self.mode,
            "priority": self.priority,
            "created_at": self.created_at,
            "status": self.status.value,
            "result": self.result,
            "error": self.error
        }


@dataclass
class InputItem:
    """输入项数据结构"""
    id: str
    question_id: str
    prompt: str
    input_value: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    status: InputStatus = InputStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "question_id": self.question_id,
            "prompt": self.prompt,
            "input_value": self.input_value,
            "created_at": self.created_at,
            "status": self.status.value
        }


class QuestionQueue:
    """问题队列管理器"""

    def __init__(self):
        self._questions: Dict[str, Question] = {}
        self._pending_queue: List[str] = []  # 按优先级排序的 ID 列表
        self._lock = asyncio.Lock()
        self._counter = 0

    async def enqueue(
        self,
        prompt: str,
        mode: str = "",
        priority: int = 0
    ) -> str:
        """加入问题到队列

        Args:
            prompt: 提示词
            mode: iflow 模式
            priority: 优先级（0 最高）

        Returns:
            问题 ID
        """
        async with self._lock:
            self._counter += 1
            question_id = f"q_{self._counter}_{int(time.time())}"

            question = Question(
                id=question_id,
                prompt=prompt,
                mode=mode,
                priority=priority
            )

            self._questions[question_id] = question

            # 按优先级插入队列
            inserted = False
            for i, qid in enumerate(self._pending_queue):
                q = self._questions[qid]
                if priority < q.priority:
                    self._pending_queue.insert(i, question_id)
                    inserted = True
                    break

            if not inserted:
                self._pending_queue.append(question_id)

            return question_id

    async def dequeue(self) -> Optional[Question]:
        """从队列取出一个问题

        Returns:
            问题对象，如果队列为空返回 None
        """
        async with self._lock:
            if not self._pending_queue:
                return None

            question_id = self._pending_queue.pop(0)
            question = self._questions[question_id]
            question.status = QuestionStatus.PROCESSING

            return question

    async def update_result(
        self,
        question_id: str,
        result: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None
    ) -> bool:
        """更新问题结果

        Args:
            question_id: 问题 ID
            result: 结果
            success: 是否成功
            error: 错误信息

        Returns:
            是否更新成功
        """
        async with self._lock:
            if question_id not in self._questions:
                return False

            question = self._questions[question_id]
            question.result = result
            question.status = QuestionStatus.COMPLETED if success else QuestionStatus.FAILED
            question.error = error

            return True

    async def get_question_status(
        self,
        question_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取单个问题的状态

        Args:
            question_id: 问题 ID

        Returns:
            问题状态信息，如果不存在返回 None
        """
        async with self._lock:
            if question_id not in self._questions:
                return None

            return self._questions[question_id].to_dict()

    async def get_status(self) -> Dict[str, Any]:
        """获取队列状态

        Returns:
            队列状态信息
        """
        async with self._lock:
            total = len(self._questions)
            pending = len(self._pending_queue)
            processing = sum(
                1 for q in self._questions.values()
                if q.status == QuestionStatus.PROCESSING
            )
            completed = sum(
                1 for q in self._questions.values()
                if q.status == QuestionStatus.COMPLETED
            )
            failed = sum(
                1 for q in self._questions.values()
                if q.status == QuestionStatus.FAILED
            )

            return {
                "total": total,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "questions": [
                    q.to_dict() for q in self._questions.values()
                ]
            }

    async def get_pending_questions(self) -> List[Question]:
        """获取所有待处理的问题

        Returns:
            待处理的问题列表
        """
        async with self._lock:
            return [
                self._questions[qid]
                for qid in self._pending_queue
            ]

    async def clear_completed(self) -> int:
        """清理已完成的问题

        Returns:
            清理的问题数量
        """
        async with self._lock:
            to_remove = [
                qid for qid, q in self._questions.items()
                if q.status in [QuestionStatus.COMPLETED, QuestionStatus.FAILED]
            ]

            for qid in to_remove:
                del self._questions[qid]

            return len(to_remove)


class InputQueue:
    """输入队列管理器"""

    def __init__(self):
        self._inputs: Dict[str, InputItem] = {}
        self._pending_inputs: List[str] = []  # 按时间顺序的 ID 列表
        self._lock = asyncio.Lock()
        self._counter = 0

    async def request_input(
        self,
        question_id: str,
        prompt: str
    ) -> str:
        """请求输入

        Args:
            question_id: 关联的问题 ID
            prompt: 提示信息

        Returns:
            输入项 ID
        """
        async with self._lock:
            self._counter += 1
            input_id = f"i_{self._counter}_{int(time.time())}"

            input_item = InputItem(
                id=input_id,
                question_id=question_id,
                prompt=prompt
            )

            self._inputs[input_id] = input_item
            self._pending_inputs.append(input_id)

            return input_id

    async def provide_input(
        self,
        input_id: str,
        value: str
    ) -> bool:
        """提供输入

        Args:
            input_id: 输入项 ID
            value: 输入值

        Returns:
            是否提供成功
        """
        async with self._lock:
            if input_id not in self._inputs:
                return False

            input_item = self._inputs[input_id]
            input_item.input_value = value
            input_item.status = InputStatus.PROVIDED

            return True

    async def consume_input(self, input_id: str) -> Optional[str]:
        """消费输入

        Args:
            input_id: 输入项 ID

        Returns:
            输入值，如果不存在返回 None
        """
        async with self._lock:
            if input_id not in self._inputs:
                return None

            input_item = self._inputs[input_id]
            if input_item.status != InputStatus.PROVIDED:
                return None

            input_item.status = InputStatus.CONSUMED

            # 从待处理列表中移除
            if input_id in self._pending_inputs:
                self._pending_inputs.remove(input_id)

            return input_item.input_value

    async def wait_for_input(
        self,
        input_id: str,
        timeout: float = 60.0
    ) -> Optional[str]:
        """等待输入

        Args:
            input_id: 输入项 ID
            timeout: 超时时间（秒）

        Returns:
            输入值，如果超时返回 None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            async with self._lock:
                if input_id not in self._inputs:
                    return None

                input_item = self._inputs[input_id]
                if input_item.status == InputStatus.PROVIDED:
                    input_item.status = InputStatus.CONSUMED
                    if input_id in self._pending_inputs:
                        self._pending_inputs.remove(input_id)
                    return input_item.input_value

            await asyncio.sleep(0.1)

        return None

    async def get_status(self) -> Dict[str, Any]:
        """获取输入队列状态

        Returns:
            输入队列状态信息
        """
        async with self._lock:
            total = len(self._inputs)
            pending = len(self._pending_inputs)
            provided = sum(
                1 for i in self._inputs.values()
                if i.status == InputStatus.PROVIDED
            )
            consumed = sum(
                1 for i in self._inputs.values()
                if i.status == InputStatus.CONSUMED
            )

            return {
                "total": total,
                "pending": pending,
                "provided": provided,
                "consumed": consumed,
                "inputs": [
                    i.to_dict() for i in self._inputs.values()
                ]
            }

    async def get_pending_inputs(self) -> List[InputItem]:
        """获取所有待处理的输入

        Returns:
            待处理的输入列表
        """
        async with self._lock:
            return [
                self._inputs[iid]
                for iid in self._pending_inputs
            ]

    async def clear_consumed(self) -> int:
        """清理已消费的输入

        Returns:
            清理的输入数量
        """
        async with self._lock:
            to_remove = [
                iid for iid, i in self._inputs.items()
                if i.status == InputStatus.CONSUMED
            ]

            for iid in to_remove:
                del self._inputs[iid]

            return len(to_remove)