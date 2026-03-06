#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动 Dev-Bot 自我迭代

让 Dev-Bot 持续自我改进
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dev_bot.self_iteration_simple import SimpleSelfIteration


async def main():
    """主函数"""
    print("="*70)
    print("Dev-Bot 自我迭代系统")
    print("="*70)
    print()
    print("Dev-Bot 将持续分析自身状态，自主决定改进方向并执行。")
    print("每次迭代包括：观察 → AI 分析决策 → AI 执行 → 验证")
    print()
    print("迭代日志保存在: .dev-bot-evolution/iteration_log.json")
    print()
    print("按 Ctrl+C 停止迭代")
    print("="*70)
    print()

    # 创建迭代系统
    iteration = SimpleSelfIteration(project_root)

    # 启动连续迭代（默认 30 分钟一次）
    interval = 1800  # 30 分钟

    print(f"启动连续迭代模式，间隔 {interval} 秒（30 分钟）")
    print()

    try:
        await iteration.start_continuous_iteration(interval=interval)
    except KeyboardInterrupt:
        print("\n")
        print("="*70)
        print("迭代已停止")
        print("="*70)
    finally:
        iteration.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDev-Bot 自我迭代已停止")
        sys.exit(0)