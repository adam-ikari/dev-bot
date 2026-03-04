#!/usr/bin/env python3

"""
自动重启管理器测试
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dev_bot.auto_restart import AutoRestartManager, get_restart_manager


def test_auto_restart_manager():
    """测试自动重启管理器"""
    print("测试自动重启管理器...")

    # 使用临时目录进行测试
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        manager = AutoRestartManager(temp_path)

        # 测试 1: 记录启动信息
        print("  测试 1: 记录启动信息...")
        startup_info = manager.record_startup("python", ["-m", "dev_bot", "run"])
        assert startup_info["command"] == "python"
        assert startup_info["args"] == ["-m", "dev_bot", "run"]
        assert startup_info["restart_count"] == 1
        print("    ✓ 启动信息记录成功")

        # 测试 2: 记录崩溃信息
        print("  测试 2: 记录崩溃信息...")
        crash_log = manager.record_crash(
            "ValueError",
            "测试错误消息",
            "测试堆栈跟踪"
        )
        assert crash_log.exists()
        print("    ✓ 崩溃日志记录成功")

        # 测试 3: 加载重启信息
        print("  测试 3: 加载重启信息...")
        restart_info = manager._load_restart_info()
        assert restart_info is not None
        assert restart_info["command"] == "python"
        print("    ✓ 重启信息加载成功")

        # 测试 4: 获取重启次数
        print("  测试 4: 获取重启次数...")
        restart_count = manager._get_restart_count()
        assert restart_count == 1
        print("    ✓ 重启次数获取成功")

        # 测试 5: 默认重启策略
        print("  测试 5: 默认重启策略...")
        strategy = manager._get_default_restart_strategy({
            "error_type": "RuntimeError",
            "error_message": "测试错误"
        })
        assert strategy["should_restart"] == True
        assert strategy["restart_strategy"] == "delayed"
        print("    ✓ 默认重启策略生成成功")

        # 测试 6: 需要人工干预的错误
        print("  测试 6: 需要人工干预的错误...")
        strategy = manager._get_default_restart_strategy({
            "error_type": "AuthenticationError",
            "error_message": "需要登录"
        })
        assert strategy["should_restart"] == False
        assert strategy["restart_strategy"] == "manual"
        print("    ✓ 人工干预策略生成成功")

        # 测试 7: 防止无限重启
        print("  测试 7: 防止无限重启...")
        for i in range(4):
            manager.record_startup("python", ["-m", "dev_bot", "run"])

        strategy = manager._get_default_restart_strategy({
            "error_type": "RuntimeError",
            "error_message": "测试错误"
        })
        assert strategy["should_restart"] == False
        assert strategy["restart_strategy"] == "manual"
        print("    ✓ 无限重启防护成功")

        print("\n✅ 所有测试通过!")


def test_get_restart_manager():
    """测试获取重启管理器实例"""
    print("\n测试获取重启管理器实例...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 测试 1: 使用指定路径
        print("  测试 1: 使用指定路径...")
        manager = get_restart_manager(temp_path)
        assert manager.project_root == temp_path
        print("    ✓ 指定路径实例创建成功")

        # 测试 2: 使用默认路径
        print("  测试 2: 使用默认路径...")
        os.chdir(temp_dir)
        manager = get_restart_manager()
        assert manager.project_root == Path.cwd()
        print("    ✓ 默认路径实例创建成功")

        print("\n✅ 所有测试通过!")


def test_restart_history():
    """测试重启历史记录"""
    print("\n测试重启历史记录...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        manager = AutoRestartManager(temp_path)

        # 记录多次启动
        print("  记录多次启动...")
        for i in range(3):
            manager.record_startup("python", ["-m", "dev_bot", "run"])

            # 记录重启历史
            strategy = {
                "should_restart": True,
                "restart_strategy": "delayed",
                "reason": "测试"
            }
            manager._record_restart_history(
                {"restart_count": i + 1},
                strategy
            )

        # 加载重启历史
        print("  加载重启历史...")
        history = manager._load_restart_history()
        assert len(history) == 3
        print("    ✓ 重启历史记录成功")

        print("\n✅ 所有测试通过!")


if __name__ == "__main__":
    try:
        test_auto_restart_manager()
        test_get_restart_manager()
        test_restart_history()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！自动重启功能正常工作！")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
