#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test process cleanup functionality

Verify proper startup and cleanup of iflow processes
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from dev_bot.iflow_manager import get_iflow_manager, IFlowMode


async def test_process_cleanup():
    """测试进程清理"""
    print("=" * 60)
    print("测试 iflow 进程清理功能")
    print("=" * 60)
    
    # 获取 iflow 管理器
    iflow_manager = get_iflow_manager(
        iflow_command="iflow",
        default_timeout=10,  # 短超时用于测试
        max_retries=1
    )
    
    print("\n[测试 1] 正常调用（预期成功）")
    print("-" * 60)
    result = await iflow_manager.call(
        prompt="Say hello",
        mode=IFlowMode.NORMAL,
        timeout=30
    )
    print(f"成功: {result.success}")
    print(f"输出: {result.output[:100]}...")
    
    print("\n[测试 2] 超时调用（预期超时并清理进程）")
    print("-" * 60)
    result = await iflow_manager.call(
        prompt="Wait for 100 seconds",
        mode=IFlowMode.NORMAL,
        timeout=5  # 5 秒超时
    )
    print(f"成功: {result.success}")
    print(f"错误: {result.error}")
    
    # 等待一下，确保进程被清理
    await asyncio.sleep(2)
    
    print("\n[测试 3] 检查进程泄漏")
    print("-" * 60)
    import subprocess
    result = subprocess.run(
        ['ps', 'aux'],
        capture_output=True,
        text=True
    )
    
    node_count = 0
    for line in result.stdout.split('\n'):
        if 'node' in line and 'iflow' in line and 'grep' not in line:
            node_count += 1
            print(f"发现 Node 进程: {line[:80]}...")
    
    print(f"\n当前 Node 进程数量: {node_count}")
    print(f"预期数量: 2 (守护进程 + AI 循环实例)")
    
    if node_count <= 2:
        print("✓ 进程清理测试通过")
    else:
        print(f"✗ 进程清理测试失败：发现 {node_count - 2} 个泄漏进程")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    # 显示统计信息
    stats = iflow_manager.get_statistics()
    print("\n调用统计:")
    print(f"  总调用次数: {stats['call_count']}")
    print(f"  成功次数: {stats['success_count']}")
    print(f"  失败次数: {stats['failure_count']}")
    print(f"  成功率: {stats['success_rate']:.1%}")


if __name__ == '__main__':
    try:
        asyncio.run(test_process_cleanup())
    except KeyboardInterrupt:
        print("\n测试已中断")