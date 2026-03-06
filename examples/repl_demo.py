#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REPL 模式演示脚本

展示如何使用 REPL 模式 + 问题队列 + 输入队列
"""
import asyncio
import sys
from pathlib import Path

# 添加 dev_bot 到路径
dev_bot_path = Path(__file__).parent.parent
if str(dev_bot_path) not in sys.path:
    sys.path.insert(0, str(dev_bot_path))

from dev_bot.repl_core import REPLCore


async def demo_basic_usage():
    """演示基本用法"""
    print("=" * 60)
    print("REPL 模式基本用法演示")
    print("=" * 60)

    # 创建 REPL 核心
    repl = REPLCore()

    # 启动 REPL
    await repl.start()
    print("[演示] REPL 已启动\n")

    # 提交几个问题
    print("[演示] 提交问题到队列...")
    q1 = await repl.submit_question("分析项目结构", mode="--plan")
    print(f"  问题 1 ID: {q1}")

    q2 = await repl.submit_question("优化性能", mode="--thinking", priority=0)
    print(f"  问题 2 ID: {q2} (高优先级)")

    q3 = await repl.submit_question("编写文档", mode="-y", priority=1)
    print(f"  问题 3 ID: {q3}\n")

    # 查看队列状态
    print("[演示] 查看队列状态...")
    status = await repl.get_queue_status()
    q_status = status["question_queue"]
    print(f"  待处理: {q_status['pending']}")
    print(f"  处理中: {q_status['processing']}\n")

    # 等待一段时间让问题被处理
    print("[演示] 等待问题处理...")
    await asyncio.sleep(2)

    # 再次查看状态
    print("[演示] 再次查看队列状态...")
    status = await repl.get_queue_status()
    q_status = status["question_queue"]
    print(f"  待处理: {q_status['pending']}")
    print(f"  已完成: {q_status['completed']}")
    print(f"  失败: {q_status['failed']}\n")

    # 停止 REPL
    await repl.stop()
    print("[演示] REPL 已停止\n")


async def demo_input_queue():
    """演示输入队列用法"""
    print("=" * 60)
    print("输入队列演示")
    print("=" * 60)

    # 创建 REPL 核心
    repl = REPLCore()
    await repl.start()
    print("[演示] REPL 已启动\n")

    # 请求输入
    print("[演示] 请求用户输入...")
    i1 = await repl.request_input("q_1", "请输入 API Key")
    print(f"  输入请求 ID: {i1}")

    i2 = await repl.request_input("q_2", "请确认是否继续 (yes/no)")
    print(f"  输入请求 ID: {i2}\n")

    # 查看输入队列状态
    print("[演示] 查看输入队列状态...")
    status = await repl.get_queue_status()
    i_status = status["input_queue"]
    print(f"  待输入: {i_status['pending']}\n")

    # 提供输入
    print("[演示] 提供输入...")
    await repl.provide_input(i1, "my-secret-key-123")
    print(f"  已提供输入: {i1}")

    await repl.provide_input(i2, "yes")
    print(f"  已提供输入: {i2}\n")

    # 等待消费
    print("[演示] 模拟消费输入...")
    value1 = await repl.wait_for_input(i1, timeout=1.0)
    print(f"  消费值: {value1}")

    value2 = await repl.wait_for_input(i2, timeout=1.0)
    print(f"  消费值: {value2}\n")

    # 查看最终状态
    print("[演示] 查看最终状态...")
    status = await repl.get_queue_status()
    i_status = status["input_queue"]
    print(f"  已消费: {i_status['consumed']}\n")

    await repl.stop()
    print("[演示] REPL 已停止\n")


async def demo_priority_queue():
    """演示优先级队列"""
    print("=" * 60)
    print("优先级队列演示")
    print("=" * 60)

    # 创建 REPL 核心
    repl = REPLCore()
    await repl.start()
    print("[演示] REPL 已启动\n")

    # 提交不同优先级的问题
    print("[演示] 提交不同优先级的问题...")
    q1 = await repl.submit_question("低优先级任务", priority=2)
    print(f"  {q1}: 优先级 2 (低)")

    q2 = await repl.submit_question("高优先级任务", priority=0)
    print(f"  {q2}: 优先级 0 (高)")

    q3 = await repl.submit_question("中优先级任务", priority=1)
    print(f"  {q3}: 优先级 1 (中)")

    q4 = await repl.submit_question("另一个高优先级任务", priority=0)
    print(f"  {q4}: 优先级 0 (高)\n")

    # 查看待处理问题（按优先级排序）
    print("[演示] 查看待处理问题（应按优先级排序）...")
    pending = await repl.question_queue.get_pending_questions()
    for i, q in enumerate(pending):
        print(f"  {i+1}. [{q.id}] {q.prompt} (优先级: {q.priority})")

    print()

    await repl.stop()
    print("[演示] REPL 已停止\n")


async def demo_clear_completed():
    """演示清理已完成任务"""
    print("=" * 60)
    print("清理已完成任务演示")
    print("=" * 60)

    # 创建 REPL 核心
    repl = REPLCore()
    await repl.start()
    print("[演示] REPL 已启动\n")

    # 提交问题
    print("[演示] 提交问题...")
    q1 = await repl.submit_question("任务 1")
    q2 = await repl.submit_question("任务 2")
    q3 = await repl.submit_question("任务 3")
    print(f"  已提交 3 个问题\n")

    # 模拟处理
    print("[演示] 模拟处理...")
    for _ in range(3):
        q = await repl.question_queue.dequeue()
        if q:
            await repl.question_queue.update_result(q.id, {"success": True})

    # 查看状态
    status = await repl.get_queue_status()
    q_status = status["question_queue"]
    print(f"  处理前: 总计 {q_status['total']}, 已完成 {q_status['completed']}\n")

    # 清理
    print("[演示] 清理已完成任务...")
    cleared = await repl.clear_completed()
    print(f"  已清理: {cleared}\n")

    # 查看清理后状态
    status = await repl.get_queue_status()
    q_status = status["question_queue"]
    print(f"  清理后: 总计 {q_status['total']}, 已完成 {q_status['completed']}\n")

    await repl.stop()
    print("[演示] REPL 已停止\n")


async def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Dev-Bot REPL 模式演示" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    # 运行所有演示
    await demo_basic_usage()
    await demo_input_queue()
    await demo_priority_queue()
    await demo_clear_completed()

    print("=" * 60)
    print("所有演示完成！")
    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
