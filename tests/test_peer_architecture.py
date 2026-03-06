"""测试平级架构

测试 AI 守护和 AI 循环的平级架构
"""
import pytest
import asyncio
from pathlib import Path

from dev_bot.output_router import (
    OutputRouter,
    OutputSource,
    LogLevel,
    OutputMessage
)


@pytest.mark.asyncio
async def test_output_router_emit():
    """测试输出路由器发送消息"""
    router = OutputRouter()

    await router.emit(
        OutputSource.GUARDIAN,
        LogLevel.INFO,
        "测试消息"
    )

    messages = await router.get_messages(limit=10)
    assert len(messages) == 1
    assert messages[0].source == OutputSource.GUARDIAN
    assert messages[0].level == LogLevel.INFO
    assert messages[0].message == "测试消息"


@pytest.mark.asyncio
async def test_output_router_multiple_sources():
    """测试多源输出"""
    router = OutputRouter()

    await router.emit_guardian(LogLevel.INFO, "守护消息")
    await router.emit_ai_loop(LogLevel.INFO, "循环消息")
    await router.emit_system(LogLevel.INFO, "系统消息")

    messages = await router.get_messages()
    assert len(messages) == 3

    # 按源过滤
    guardian_msgs = await router.get_messages(source=OutputSource.GUARDIAN)
    assert len(guardian_msgs) == 1
    assert guardian_msgs[0].message == "守护消息"

    ai_loop_msgs = await router.get_messages(source=OutputSource.AI_LOOP)
    assert len(ai_loop_msgs) == 1
    assert ai_loop_msgs[0].message == "循环消息"


@pytest.mark.asyncio
async def test_output_router_filter_by_level():
    """测试按级别过滤"""
    router = OutputRouter()

    await router.emit(OutputSource.SYSTEM, LogLevel.INFO, "信息")
    await router.emit(OutputSource.SYSTEM, LogLevel.WARNING, "警告")
    await router.emit(OutputSource.SYSTEM, LogLevel.ERROR, "错误")

    # 获取所有错误
    error_msgs = await router.get_messages(level=LogLevel.ERROR)
    assert len(error_msgs) == 1
    assert error_msgs[0].message == "错误"

    # 获取所有警告
    warning_msgs = await router.get_messages(level=LogLevel.WARNING)
    assert len(warning_msgs) == 1
    assert warning_msgs[0].message == "警告"


@pytest.mark.asyncio
async def test_output_router_subscribe():
    """测试订阅机制"""
    router = OutputRouter()
    received_messages = []

    def callback(msg):
        received_messages.append(msg)

    router.subscribe(callback)

    await router.emit(OutputSource.SYSTEM, LogLevel.INFO, "测试")

    await asyncio.sleep(0.1)  # 等待回调

    assert len(received_messages) == 1
    assert received_messages[0].message == "测试"

    # 取消订阅
    router.unsubscribe(callback)

    await router.emit(OutputSource.SYSTEM, LogLevel.INFO, "测试2")

    assert len(received_messages) == 1  # 应该还是 1


@pytest.mark.asyncio
async def test_output_router_stats():
    """测试统计信息"""
    router = OutputRouter()

    await router.emit_guardian(LogLevel.INFO, "消息1")
    await router.emit_guardian(LogLevel.ERROR, "消息2")
    await router.emit_ai_loop(LogLevel.INFO, "消息3")
    await router.emit_ai_loop(LogLevel.WARNING, "消息4")
    await router.emit_system(LogLevel.INFO, "消息5")

    stats = await router.get_stats()

    assert stats["total"] == 5
    assert stats["by_source"]["guardian"] == 2
    assert stats["by_source"]["ai_loop"] == 2
    assert stats["by_source"]["system"] == 1
    assert stats["by_level"]["error"] == 1
    assert stats["by_level"]["warning"] == 1


@pytest.mark.asyncio
async def test_output_router_clear():
    """测试清空消息"""
    router = OutputRouter()

    await router.emit(OutputSource.SYSTEM, LogLevel.INFO, "消息1")
    await router.emit(OutputSource.SYSTEM, LogLevel.INFO, "消息2")

    messages = await router.get_messages()
    assert len(messages) == 2

    await router.clear()

    messages = await router.get_messages()
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_output_router_limit():
    """测试消息数量限制"""
    router = OutputRouter(max_history=5)

    for i in range(10):
        await router.emit(OutputSource.SYSTEM, LogLevel.INFO, f"消息{i}")

    messages = await router.get_messages()
    assert len(messages) == 5  # 只保留最近 5 条

    # 检查是否是最后 5 条
    for i, msg in enumerate(messages):
        assert msg.message == f"消息{5 + i}"


@pytest.mark.asyncio
async def test_output_message_to_dict():
    """测试消息转换为字典"""
    msg = OutputMessage(
        id="msg_1",
        source=OutputSource.GUARDIAN,
        level=LogLevel.INFO,
        timestamp=1234567890.0,
        message="测试消息",
        data={"key": "value"}
    )

    data = msg.to_dict()

    assert data["id"] == "msg_1"
    assert data["source"] == "guardian"
    assert data["level"] == "info"
    assert data["timestamp"] == 1234567890.0
    assert data["message"] == "测试消息"
    assert data["data"] == {"key": "value"}


def test_output_source_enum():
    """测试输出源枚举"""
    assert OutputSource.GUARDIAN.value == "guardian"
    assert OutputSource.AI_LOOP.value == "ai_loop"
    assert OutputSource.SYSTEM.value == "system"


def test_log_level_enum():
    """测试日志级别枚举"""
    assert LogLevel.DEBUG.value == "debug"
    assert LogLevel.INFO.value == "info"
    assert LogLevel.WARNING.value == "warning"
    assert LogLevel.ERROR.value == "error"
    assert LogLevel.SUCCESS.value == "success"


@pytest.mark.asyncio
async def test_global_output_router():
    """测试全局输出路由器"""
    from dev_bot.output_router import get_output_router, reset_output_router

    # 重置
    reset_output_router()

    # 获取实例
    router1 = get_output_router()
    router2 = get_output_router()

    # 应该是同一个实例
    assert router1 is router2

    # 发送消息
    await router1.emit(OutputSource.SYSTEM, LogLevel.INFO, "测试")

    # 从另一个实例获取
    messages = await router2.get_messages()
    assert len(messages) == 1
    assert messages[0].message == "测试"

    # 重置
    reset_output_router()

    # 获取新实例
    router3 = get_output_router()
    assert router3 is not router1

    # 应该没有消息
    messages = await router3.get_messages()
    assert len(messages) == 0