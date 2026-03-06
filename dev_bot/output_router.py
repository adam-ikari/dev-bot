"""输出路由器

将 AI 守护和 AI 循环的输出路由到用户交互层
"""
import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from collections import deque


class OutputSource(Enum):
    """输出源"""
    GUARDIAN = "guardian"  # AI 守护
    AI_LOOP = "ai_loop"  # AI 循环
    SYSTEM = "system"  # 系统消息


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class OutputMessage:
    """输出消息"""
    id: str
    source: OutputSource
    level: LogLevel
    timestamp: float
    message: str
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "source": self.source.value,
            "level": self.level.value,
            "timestamp": self.timestamp,
            "message": self.message,
            "data": self.data
        }


class OutputRouter:
    """输出路由器

    管理所有输出消息，并提供订阅机制
    """

    def __init__(self, max_history: int = 1000):
        self._messages: deque[OutputMessage] = deque(maxlen=max_history)
        self._subscribers: List[Callable] = []
        self._lock = asyncio.Lock()
        self._counter = 0

    async def emit(
        self,
        source: OutputSource,
        level: LogLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """发送输出消息

        Args:
            source: 输出源
            level: 日志级别
            message: 消息内容
            data: 附加数据
        """
        async with self._lock:
            self._counter += 1
            msg = OutputMessage(
                id=f"msg_{self._counter}_{int(time.time())}",
                source=source,
                level=level,
                timestamp=time.time(),
                message=message,
                data=data
            )

            self._messages.append(msg)

        # 通知订阅者
        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(msg)
                else:
                    callback(msg)
            except Exception as e:
                print(f"[输出路由器] 通知订阅者失败: {e}")

    async def emit_guardian(
        self,
        level: LogLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """发送守护输出"""
        await self.emit(OutputSource.GUARDIAN, level, message, data)

    async def emit_ai_loop(
        self,
        level: LogLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """发送 AI 循环输出"""
        await self.emit(OutputSource.AI_LOOP, level, message, data)

    async def emit_system(
        self,
        level: LogLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """发送系统输出"""
        await self.emit(OutputSource.SYSTEM, level, message, data)

    def subscribe(self, callback: Callable):
        """订阅输出消息

        Args:
            callback: 回调函数
        """
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        """取消订阅"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    async def get_messages(
        self,
        source: Optional[OutputSource] = None,
        level: Optional[LogLevel] = None,
        limit: int = 100,
        since: Optional[float] = None
    ) -> List[OutputMessage]:
        """获取消息

        Args:
            source: 输出源过滤
            level: 日志级别过滤
            limit: 最大数量
            since: 起始时间戳

        Returns:
            消息列表
        """
        async with self._lock:
            filtered = list(self._messages)

            # 过滤
            if source:
                filtered = [m for m in filtered if m.source == source]

            if level:
                filtered = [m for m in filtered if m.level == level]

            if since:
                filtered = [m for m in filtered if m.timestamp >= since]

            # 限制数量
            return filtered[-limit:]

    async def get_latest(self, count: int = 10) -> List[OutputMessage]:
        """获取最新消息"""
        return await self.get_messages(limit=count)

    async def clear(self):
        """清空消息"""
        async with self._lock:
            self._messages.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        async with self._lock:
            total = len(self._messages)
            guardian_count = sum(1 for m in self._messages if m.source == OutputSource.GUARDIAN)
            ai_loop_count = sum(1 for m in self._messages if m.source == OutputSource.AI_LOOP)
            system_count = sum(1 for m in self._messages if m.source == OutputSource.SYSTEM)

            error_count = sum(1 for m in self._messages if m.level == LogLevel.ERROR)
            warning_count = sum(1 for m in self._messages if m.level == LogLevel.WARNING)

            return {
                "total": total,
                "by_source": {
                    "guardian": guardian_count,
                    "ai_loop": ai_loop_count,
                    "system": system_count
                },
                "by_level": {
                    "error": error_count,
                    "warning": warning_count,
                    "info": total - error_count - warning_count
                },
                "subscribers": len(self._subscribers)
            }


class OutputCapture:
    """输出捕获器

    捕获标准输出和错误输出，并路由到输出路由器
    """

    def __init__(self, router: OutputRouter, source: OutputSource):
        self.router = router
        self.source = source
        self._original_stdout = None
        self._original_stderr = None

    def start_capture(self):
        """开始捕获输出"""
        import sys

        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

        sys.stdout = self._StdoutCapture(self.router, self.source)
        sys.stderr = self._StderrCapture(self.router, self.source)

    def stop_capture(self):
        """停止捕获输出"""
        import sys

        if self._original_stdout:
            sys.stdout = self._original_stdout
        if self._original_stderr:
            sys.stderr = self._original_stderr

    class _StdoutCapture:
        """标准输出捕获"""

        def __init__(self, router: OutputRouter, source: OutputSource):
            self.router = router
            self.source = source

        def write(self, text):
            if text.strip():
                asyncio.create_task(
                    self.router.emit(self.source, LogLevel.INFO, text.strip())
                )

        def flush(self):
            pass

    class _StderrCapture:
        """标准错误捕获"""

        def __init__(self, router: OutputRouter, source: OutputSource):
            self.router = router
            self.source = source

        def write(self, text):
            if text.strip():
                asyncio.create_task(
                    self.router.emit(self.source, LogLevel.ERROR, text.strip())
                )

        def flush(self):
            pass


# 全局输出路由器实例
_global_output_router = None


def get_output_router() -> OutputRouter:
    """获取全局输出路由器实例"""
    global _global_output_router

    if _global_output_router is None:
        _global_output_router = OutputRouter()

    return _global_output_router


def reset_output_router():
    """重置全局输出路由器"""
    global _global_output_router
    _global_output_router = None