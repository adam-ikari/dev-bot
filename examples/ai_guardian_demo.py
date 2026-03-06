#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 守护监控演示脚本

展示 AI 守护监视 AI 循环的功能
"""
import asyncio
import sys
from pathlib import Path

# 添加 dev_bot 到路径
dev_bot_path = Path(__file__).parent.parent
if str(dev_bot_path) not in sys.path:
    sys.path.insert(0, str(dev_bot_path))

from dev_bot.ai_guardian_monitor import AIGuardianMonitor
from dev_bot.output_router import (
    get_output_router,
    reset_output_router,
    OutputSource,
    LogLevel
)


async def demo_basic_monitoring():
    """演示基本监控功能"""
    print("=" * 60)
    print("基本监控功能演示")
    print("=" * 60)

    reset_output_router()
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root, check_interval=2)

    print("\n[演示] 启动 AI 守护监控...")
    await monitor.start()

    # 等待 AI 循环启动
    await asyncio.sleep(2)

    # 查看状态
    status = await monitor.get_status()
    print(f"[演示] AI 循环 PID: {status['ai_loop']['pid']}")
    print(f"[演示] AI 循环健康: {status['ai_loop']['healthy']}")

    # 等待一段时间
    print("[演示] 监控 5 秒...")
    await asyncio.sleep(5)

    # 查看输出
    print("\n[演示] 查看 AI 守护输出...")
    messages = await get_output_router().get_messages(
        source=OutputSource.GUARDIAN,
        limit=10
    )

    for msg in messages:
        print(f"  [{msg.level.value}] {msg.message}")

    # 停止监控
    print("\n[演示] 停止 AI 守护监控...")
    await monitor.stop()

    reset_output_router()
    print("[演示] 演示完成\n")


async def demo_health_check():
    """演示健康检查功能"""
    print("=" * 60)
    print("健康检查演示")
    print("=" * 60)

    reset_output_router()
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root, check_interval=1)

    print("\n[演示] 启动监控...")
    await monitor.start()

    # 等待 AI 循环启动
    await asyncio.sleep(2)

    # 检查健康状态
    print("[演示] 检查 AI 循环健康状态...")
    await monitor._check_ai_loop_health()

    status = await monitor.get_status()
    print(f"  健康状态: {status['ai_loop']['healthy']}")
    print(f"  最后检查: {status['ai_loop']['last_check']}")

    # 停止监控
    await monitor.stop()
    reset_output_router()
    print("[演示] 演示完成\n")


async def demo_restart_simulation():
    """演示重启模拟"""
    print("=" * 60)
    print("重启模拟演示")
    print("=" * 60)

    reset_output_router()
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root, check_interval=1)

    print("\n[演示] 启动监控...")
    await monitor.start()

    # 等待 AI 循环启动
    await asyncio.sleep(2)

    print("[演示] 模拟 AI 循环崩溃...")
    if monitor.ai_loop_process:
        try:
            monitor.ai_loop_process.kill()
            monitor.ai_loop_process.wait(timeout=5)
        except:
            pass
        monitor.ai_loop_process = None
        monitor.ai_loop_pid = None

    print("[演示] 等待守护检测到崩溃并重启...")
    await asyncio.sleep(5)

    # 查看状态
    status = await monitor.get_status()
    print(f"  重启次数: {status['ai_loop']['restart_count']}")
    print(f"  当前 PID: {status['ai_loop']['pid']}")
    print(f"  健康状态: {status['ai_loop']['healthy']}")

    # 停止监控
    await monitor.stop()
    reset_output_router()
    print("[演示] 演示完成\n")


async def demo_output_routing():
    """演示输出路由"""
    print("=" * 60)
    print("输出路由演示")
    print("=" * 60)

    reset_output_router()
    output_router = get_output_router()
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root, check_interval=2)

    print("\n[演示] 启动监控...")
    await monitor.start()

    # 等待一些输出
    print("[演示] 等待输出...")
    await asyncio.sleep(3)

    # 查看所有输出
    print("\n[演示] 查看所有输出...")
    all_messages = await output_router.get_messages(limit=20)
    print(f"  总消息数: {len(all_messages)}")

    # 按源分类
    guardian_msgs = await output_router.get_messages(source=OutputSource.GUARDIAN)
    ai_loop_msgs = await output_router.get_messages(source=OutputSource.AI_LOOP)

    print(f"  AI 守护消息: {len(guardian_msgs)}")
    print(f"  AI 循环消息: {len(ai_loop_msgs)}")

    # 显示最新的几条
    print("\n[演示] 最新消息:")
    for msg in all_messages[-5:]:
        source_symbol = {
            OutputSource.GUARDIAN: "🛡️",
            OutputSource.AI_LOOP: "🔄",
            OutputSource.SYSTEM: "⚙️"
        }.get(msg.source, "?")

        print(f"  {source_symbol} [{msg.source.value}] {msg.message}")

    # 停止监控
    await monitor.stop()
    reset_output_router()
    print("[演示] 演示完成\n")


async def demo_max_restarts():
    """演示最大重启次数限制"""
    print("=" * 60)
    print("最大重启次数限制演示")
    print("=" * 60)

    reset_output_router()
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root, check_interval=1)

    # 设置最大重启次数
    monitor.max_restarts = 2

    print("\n[演示] 启动监控（最大重启次数: 2）...")
    await monitor.start()

    # 等待 AI 循环启动
    await asyncio.sleep(2)

    # 模拟多次崩溃
    print("[演示] 模拟多次崩溃...")
    for i in range(3):
        if monitor.ai_loop_process:
            try:
                monitor.ai_loop_process.kill()
                monitor.ai_loop_process.wait(timeout=5)
            except:
                pass
            monitor.ai_loop_process = None
            monitor.ai_loop_pid = None

        print(f"  第 {i+1} 次崩溃...")
        await asyncio.sleep(3)

    # 查看状态
    status = await monitor.get_status()
    print(f"\n[演示] 最终状态:")
    print(f"  重启次数: {status['ai_loop']['restart_count']}")
    print(f"  最大重启次数: {monitor.max_restarts}")
    print(f"  健康状态: {status['ai_loop']['healthy']}")

    # 停止监控
    await monitor.stop()
    reset_output_router()
    print("[演示] 演示完成\n")


async def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "AI 守护监控演示" + " " * 26 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    # 运行所有演示
    await demo_basic_monitoring()
    await demo_health_check()
    await demo_output_routing()
    await demo_max_restarts()
    # 重启模拟演示可能会启动真实进程，最后运行
    # await demo_restart_simulation()

    print("=" * 60)
    print("所有演示完成！")
    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
