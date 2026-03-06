#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平级架构演示脚本

展示 AI 守护和 AI 循环的平级架构
"""
import asyncio
import sys
from pathlib import Path

# 添加 dev_bot 到路径
dev_bot_path = Path(__file__).parent.parent
if str(dev_bot_path) not in sys.path:
    sys.path.insert(0, str(dev_bot_path))

from dev_bot.output_router import (
    get_output_router,
    reset_output_router,
    OutputSource,
    LogLevel
)


async def demo_output_router():
    """演示输出路由器"""
    print("=" * 60)
    print("输出路由器演示")
    print("=" * 60)

    router = get_output_router()

    # 发送不同源的输出
    print("\n[演示] 发送不同源的输出...")
    await router.emit_guardian(LogLevel.INFO, "守护进程启动")
    await router.emit_ai_loop(LogLevel.INFO, "AI 循环启动")
    await router.emit_system(LogLevel.SUCCESS, "系统初始化完成")

    # 发送不同级别的输出
    print("[演示] 发送不同级别的输出...")
    await router.emit_guardian(LogLevel.DEBUG, "调试信息")
    await router.emit_ai_loop(LogLevel.WARNING, "警告信息")
    await router.emit_system(LogLevel.ERROR, "错误信息")

    # 查看所有输出
    print("\n[演示] 查看所有输出...")
    messages = await router.get_messages()
    print(f"  共 {len(messages)} 条消息")

    for msg in messages:
        source_symbol = {
            OutputSource.GUARDIAN: "🛡️",
            OutputSource.AI_LOOP: "🔄",
            OutputSource.SYSTEM: "⚙️"
        }.get(msg.source, "?")

        level_symbol = {
            LogLevel.DEBUG: "🔍",
            LogLevel.INFO: "ℹ️",
            LogLevel.WARNING: "⚠️",
            LogLevel.ERROR: "❌",
            LogLevel.SUCCESS: "✅"
        }.get(msg.level, "?")

        print(f"  {source_symbol} {level_symbol} [{msg.source.value}] {msg.message}")

    # 按源过滤
    print("\n[演示] 按源过滤（AI 守护）...")
    guardian_msgs = await router.get_messages(source=OutputSource.GUARDIAN)
    print(f"  AI 守护消息: {len(guardian_msgs)} 条")
    for msg in guardian_msgs:
        print(f"    - {msg.message}")

    # 按级别过滤
    print("\n[演示] 按级别过滤（错误）...")
    error_msgs = await router.get_messages(level=LogLevel.ERROR)
    print(f"  错误消息: {len(error_msgs)} 条")
    for msg in error_msgs:
        print(f"    - {msg.message}")

    # 统计信息
    print("\n[演示] 统计信息...")
    stats = await router.get_stats()
    print(f"  总计: {stats['total']}")
    print(f"  按源: {stats['by_source']}")
    print(f"  按级别: {stats['by_level']}")

    # 清空
    print("\n[演示] 清空消息...")
    await router.clear()
    messages = await router.get_messages()
    print(f"  清空后: {len(messages)} 条消息")

    # 重置
    reset_output_router()
    print("[演示] 演示完成\n")


async def demo_subscribe():
    """演示订阅机制"""
    print("=" * 60)
    print("订阅机制演示")
    print("=" * 60)

    router = get_output_router()
    received = []

    def callback(msg):
        received.append(msg)
        print(f"  [订阅回调] 收到消息: {msg.message}")

    # 订阅
    print("\n[演示] 订阅输出...")
    router.subscribe(callback)

    # 发送消息
    print("[演示] 发送消息...")
    await router.emit_guardian(LogLevel.INFO, "消息1")
    await router.emit_ai_loop(LogLevel.INFO, "消息2")
    await asyncio.sleep(0.1)

    print(f"\n[演示] 收到 {len(received)} 条消息")

    # 取消订阅
    print("\n[演示] 取消订阅...")
    router.unsubscribe(callback)

    # 发送新消息
    print("[演示] 发送新消息（应该不会收到）...")
    await router.emit_system(LogLevel.INFO, "消息3")
    await asyncio.sleep(0.1)

    print(f"  仍然收到 {len(received)} 条消息（没有增加）")

    # 重置
    reset_output_router()
    print("[演示] 演示完成\n")


async def demo_tui_integration():
    """演示 TUI 集成"""
    print("=" * 60)
    print("TUI 集成演示")
    print("=" * 60)

    from dev_bot.interaction import TUILayer

    print("\n[演示] 创建 TUI 层...")
    tui = TUILayer()

    print("[演示] TUI 层已订阅输出路由器")
    print("[演示] 模拟发送输出...")

    # 模拟 AI 守护输出
    await tui.output_router.emit_guardian(
        LogLevel.INFO,
        "守护进程检查 AI 循环健康状态"
    )
    await asyncio.sleep(0.1)

    # 模拟 AI 循环输出
    await tui.output_router.emit_ai_loop(
        LogLevel.INFO,
        "执行 AI 任务：分析项目结构"
    )
    await asyncio.sleep(0.1)

    # 模拟系统输出
    await tui.output_router.emit_system(
        LogLevel.SUCCESS,
        "任务完成"
    )
    await asyncio.sleep(0.1)

    print("\n[演示] 查看输出...")
    await tui._show_output(source=None, level=None, count=20)

    # 重置
    reset_output_router()
    print("[演示] 演示完成\n")


async def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "平级架构演示" + " " * 29 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    # 运行所有演示
    await demo_output_router()
    await demo_subscribe()
    await demo_tui_integration()

    print("=" * 60)
    print("所有演示完成！")
    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
