"""REPL 核心实现

Read-Eval-Print Loop with queue management
"""
import asyncio
import sys
from typing import Any, Dict, Optional
from .queue_manager import QuestionQueue, InputQueue
from .core import get_core


class REPLCore:
    """REPL 核心类

    管理问题队列、输入队列和执行循环
    """

    def __init__(self):
        self.question_queue = QuestionQueue()
        self.input_queue = InputQueue()
        self.core = get_core()
        self._running = False
        self._processing_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动 REPL 循环"""
        if self._running:
            return

        self._running = True

        # 启动问题处理任务
        self._processing_task = asyncio.create_task(self._process_questions())

    async def stop(self):
        """停止 REPL 循环"""
        self._running = False

        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

    async def _process_questions(self):
        """处理问题队列

        持续从队列中取出问题并执行
        """
        while self._running:
            question = await self.question_queue.dequeue()

            if question is None:
                await asyncio.sleep(0.1)
                continue

            try:
                # 执行问题
                result = await self._execute_question(question)

                # 更新结果
                await self.question_queue.update_result(
                    question.id,
                    result,
                    success=result.get("success", True),
                    error=result.get("error")
                )

            except Exception as e:
                # 更新错误
                await self.question_queue.update_result(
                    question.id,
                    {"success": False},
                    success=False,
                    error=str(e)
                )

    async def _execute_question(self, question) -> Dict[str, Any]:
        """执行问题

        Args:
            question: 问题对象

        Returns:
            执行结果
        """
        # 根据 mode 选择执行方式
        if question.mode == "--plan":
            return await self.core.plan(question.prompt)
        elif question.mode == "-y":
            return await self.core.execute(question.prompt)
        elif question.mode == "--thinking":
            return await self.core.think(question.prompt)
        else:
            return await self.core.call_iflow(question.prompt)

    async def submit_question(
        self,
        prompt: str,
        mode: str = "",
        priority: int = 0
    ) -> str:
        """提交问题

        Args:
            prompt: 提示词
            mode: iflow 模式
            priority: 优先级

        Returns:
            问题 ID
        """
        return await self.question_queue.enqueue(prompt, mode, priority)

    async def get_question_status(
        self,
        question_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取问题状态

        Args:
            question_id: 问题 ID

        Returns:
            问题状态信息
        """
        status = await self.question_queue.get_status()

        for q in status["questions"]:
            if q["id"] == question_id:
                return q

        return None

    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态

        Returns:
            队列状态信息
        """
        return {
            "question_queue": await self.question_queue.get_status(),
            "input_queue": await self.input_queue.get_status()
        }

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
        return await self.input_queue.request_input(question_id, prompt)

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
        return await self.input_queue.provide_input(input_id, value)

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
        return await self.input_queue.wait_for_input(input_id, timeout)

    async def clear_completed(self) -> Dict[str, int]:
        """清理已完成的任务

        Returns:
            清理统计
        """
        questions_cleared = await self.question_queue.clear_completed()
        inputs_cleared = await self.input_queue.clear_consumed()

        return {
            "questions": questions_cleared,
            "inputs": inputs_cleared
        }