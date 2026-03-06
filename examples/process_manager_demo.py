#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process Manager Demo

演示如何使用 ProcessManager 来管理进程
避免直接使用 python3 命令
"""

import asyncio
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.process_manager import (
    ProcessManager,
    get_process_manager,
    start_ai_loop,
    stop_ai_loop,
    start_guardian,
    stop_guardian
)


async def demo_basic_usage():
    """演示基本用法"""
    print("\n=== 演示基本用法 ===\n")
    
    # 创建进程管理器
    manager = ProcessManager()
    
    # 获取当前 Python 解释器
    python_interp = manager.get_python_interpreter()
    print(f"当前 Python 解释器: {python_interp}")
    print(f"sys.executable: {sys.executable}")
    assert python_interp == sys.executable, "应该使用 sys.executable"
    print("✓ 使用 sys.executable 而非硬编码 'python3'\n")


async def demo_process_creation():
    """演示进程创建"""
    print("\n=== 演示进程创建 ===\n")
    
    manager = ProcessManager()
    project_root = Path.cwd()
    
    # 创建一个简单的测试脚本
    test_script = project_root / "examples" / "test_script.py"
    test_script.write_text("""#!/usr/bin/env python3
import time
import sys

print("测试进程启动")
print(f"Python 版本: {sys.version}")
print(f"PID: {os.getpid()}")

# 模拟工作
for i in range(3):
    print(f"工作中... {i+1}/3")
    time.sleep(0.5)

print("测试进程完成")
""")
    
    try:
        # 使用 ProcessManager 创建进程
        # 注意：这里使用 sys.executable，而不是硬编码 'python3'
        process = await manager.create_process(
            process_id="test_process",
            script_path=test_script,
            args=[],
            cwd=project_root
        )
        
        if process:
            print(f"✓ 进程创建成功，PID: {process.pid}")
            print(f"✓ 使用命令: {sys.executable} {test_script}")
            print(f"✓ 而非: python3 {test_script}")
            
            # 等待进程完成
            await process.wait()
            print(f"✓ 进程退出码: {process.returncode}")
        
    finally:
        if test_script.exists():
            test_script.unlink()


async def demo_convenience_functions():
    """演示便捷函数"""
    print("\n=== 演示便捷函数 ===\n")
    
    project_root = Path.cwd()
    
    print("便捷函数简化了常见操作：")
    print()
    print("1. 启动 AI 循环:")
    print("   pid = await start_ai_loop(project_root, 'config.json')")
    print("   → 内部使用 sys.executable 而非 'python3'")
    print()
    print("2. 停止 AI 循环:")
    print("   success = await stop_ai_loop('ai_loop')")
    print()
    print("3. 启动守护进程:")
    print("   pid = await start_guardian(project_root, check_interval=30)")
    print("   → 内部使用 sys.executable 而非 'python3'")
    print()
    print("4. 停止守护进程:")
    print("   success = await stop_guardian('guardian')")
    print()
    print("✓ 所有便捷函数都避免直接使用 'python3' 命令")


async def demo_global_manager():
    """演示全局管理器"""
    print("\n=== 演示全局管理器 ===\n")
    
    # 重置全局管理器
    from dev_bot.process_manager import reset_process_manager
    reset_process_manager()
    
    # 获取全局实例
    manager = get_process_manager()
    print("✓ 获取全局进程管理器实例")
    print(f"✓ 类型: {type(manager)}")
    print(f"✓ Python 解释器: {manager.get_python_interpreter()}")


async def demo_process_info():
    """演示进程信息查询"""
    print("\n=== 演示进程信息查询 ===\n")
    
    manager = ProcessManager()
    project_root = Path.cwd()
    
    # 创建一个长期运行的进程
    test_script = project_root / "examples" / "long_running.py"
    test_script.write_text("""#!/usr/bin/env python3
import time
while True:
    print("运行中...")
    time.sleep(1)
""")
    
    try:
        # 创建进程
        process = await manager.create_process(
            process_id="long_process",
            script_path=test_script,
            args=[]
        )
        
        if process:
            # 查询进程信息
            info = manager.get_all_process_info()
            print(f"进程信息: {info}")
            
            # 检查进程状态
            is_running = manager.is_process_running("long_process")
            print(f"进程运行中: {is_running}")
            
            # 获取进程 PID
            pid = manager.get_process_pid("long_process")
            print(f"进程 PID: {pid}")
            
            # 获取运行中的进程数量
            count = manager.get_running_process_count()
            print(f"运行中的进程数量: {count}")
            
            # 停止进程
            success = await manager.stop_process("long_process", timeout=5)
            print(f"停止进程: {'成功' if success else '失败'}")
        
    finally:
        if test_script.exists():
            test_script.unlink()


async def main():
    """主函数"""
    print("=" * 70)
    print("Process Manager 演示")
    print("=" * 70)
    print("\n本演示展示如何使用 ProcessManager 避免直接使用 'python3' 命令")
    print("ProcessManager 内部使用 sys.executable 获取当前 Python 解释器路径")
    print("=" * 70)
    
    try:
        await demo_basic_usage()
        await demo_process_creation()
        await demo_convenience_functions()
        await demo_global_manager()
        await demo_process_info()
        
        print("\n" + "=" * 70)
        print("✓ 所有演示完成")
        print("=" * 70)
        print("\n关键要点：")
        print("1. 使用 sys.executable 而非硬编码 'python3'")
        print("2. ProcessManager 统一管理所有进程创建")
        print("3. 提供便捷函数简化常见操作")
        print("4. 支持进程信息查询和管理")
        print("5. 避免了直接命令行调用的风险")
        print()
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
