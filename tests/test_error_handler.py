#!/usr/bin/env python3

"""
统一错误处理器测试
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dev_bot.error_handler import UnifiedErrorHandler


def test_unified_error_handler_initialization():
    """测试统一错误处理器初始化"""
    print("测试统一错误处理器初始化...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建模拟配置和日志
        config = MagicMock()
        config.get_auto_restart_enabled = MagicMock(return_value=True)
        logger = MagicMock()

        # 初始化错误处理器
        handler = UnifiedErrorHandler(
            project_root=temp_path,
            config=config,
            logger=logger,
            ai_tool="iflow"
        )

        # 验证初始化
        assert handler.project_root == temp_path
        assert handler.config == config
        assert handler.logger == logger
        assert handler.ai_tool == "iflow"
        assert handler.error_count == 0
        assert handler.fix_success_count == 0
        assert handler.fix_failure_count == 0
        assert handler.restart_count == 0

        print("  ✓ 统一错误处理器初始化成功")


async def test_handle_error_with_auto_fix_enabled():
    """测试启用自动修复时的错误处理"""
    print("测试启用自动修复时的错误处理...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建模拟配置和日志
        config = MagicMock()
        config.get_auto_restart_enabled = MagicMock(return_value=True)
        logger = MagicMock()

        # 初始化错误处理器
        handler = UnifiedErrorHandler(
            project_root=temp_path,
            config=config,
            logger=logger,
            ai_tool="iflow"
        )

        # 模拟一个简单的错误
        error = ValueError("测试错误")

        # Mock 错误分析和自动修复
        handler._analyze_error = MagicMock(return_value={
            "error_type": "ValueError",
            "error_message": "测试错误",
            "error_analysis": {
                "severity": "medium",
                "description": "测试错误描述"
            },
            "suggested_fixes": []
        })
        handler._attempt_auto_fix = AsyncMock(return_value=True)
        handler._save_crash_info = MagicMock(return_value=temp_path / "crash_test.json")
        handler.restart_manager = MagicMock()
        handler.restart_manager.analyze_restart_strategy = MagicMock(return_value={
            "should_restart": False,
            "reason": "修复成功，无需重启"
        })

        # 处理错误
        result = await handler.handle_error(error)

        # 验证结果
        assert result is True  # 应该继续运行
        assert handler.error_count == 1
        assert handler.fix_success_count == 1
        assert handler.fix_failure_count == 0

        print("  ✓ 自动修复错误处理成功")


async def test_handle_error_with_auto_fix_disabled():
    """测试禁用自动修复时的错误处理"""
    print("测试禁用自动修复时的错误处理...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建模拟配置和日志
        config = MagicMock()
        config.get_auto_restart_enabled = MagicMock(return_value=False)
        logger = MagicMock()

        # 初始化错误处理器
        handler = UnifiedErrorHandler(
            project_root=temp_path,
            config=config,
            logger=logger,
            ai_tool="iflow"
        )

        # 模拟一个简单的错误
        error = ValueError("测试错误")

        # 处理错误
        result = await handler.handle_error(error)

        # 验证结果
        assert result is False  # 应该退出/重启
        assert handler.error_count == 1

        print("  ✓ 禁用自动修复的错误处理成功")


async def test_handle_error_with_fix_failure():
    """测试自动修复失败时的错误处理"""
    print("测试自动修复失败时的错误处理...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建模拟配置和日志
        config = MagicMock()
        config.get_auto_restart_enabled = MagicMock(return_value=True)
        logger = MagicMock()

        # 初始化错误处理器
        handler = UnifiedErrorHandler(
            project_root=temp_path,
            config=config,
            logger=logger,
            ai_tool="iflow"
        )

        # 模拟一个简单的错误
        error = ValueError("测试错误")

        # Mock 错误分析和自动修复（修复失败）
        handler._analyze_error = MagicMock(return_value={
            "error_type": "ValueError",
            "error_message": "测试错误",
            "error_analysis": {
                "severity": "high",
                "description": "严重错误"
            },
            "suggested_fixes": []
        })
        handler._attempt_auto_fix = AsyncMock(return_value=False)
        handler._save_crash_info = MagicMock(return_value=temp_path / "crash_test.json")
        handler.restart_manager = MagicMock()
        handler.restart_manager.analyze_restart_strategy = MagicMock(return_value={
            "should_restart": False,
            "reason": "不需要重启"
        })

        # 处理错误
        result = await handler.handle_error(error)

        # 验证结果
        assert result is True  # 不需要重启，可以继续
        assert handler.error_count == 1
        assert handler.fix_success_count == 0
        assert handler.fix_failure_count == 1

        print("  ✓ 自动修复失败的错误处理成功")


def test_save_crash_info():
    """测试保存崩溃信息"""
    print("测试保存崩溃信息...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建模拟配置和日志
        config = MagicMock()
        logger = MagicMock()

        # 初始化错误处理器
        handler = UnifiedErrorHandler(
            project_root=temp_path,
            config=config,
            logger=logger,
            ai_tool="iflow"
        )

        # 模拟一个错误
        error = ValueError("测试错误")
        analysis = {
            "error_type": "ValueError",
            "error_message": "测试错误"
        }
        context = {"session": 1}

        # 保存崩溃信息
        crash_log_file = handler._save_crash_info(error, analysis, context)

        # 验证文件存在
        assert crash_log_file.exists()

        # 验证文件内容
        with open(crash_log_file, encoding='utf-8') as f:
            crash_info = json.load(f)
            assert crash_info["error_type"] == "ValueError"
            assert crash_info["error_message"] == "测试错误"
            assert crash_info["session"] == 1

        print("  ✓ 崩溃信息保存成功")


def test_get_statistics():
    """测试获取统计信息"""
    print("测试获取统计信息...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建模拟配置和日志
        config = MagicMock()
        logger = MagicMock()

        # 初始化错误处理器
        handler = UnifiedErrorHandler(
            project_root=temp_path,
            config=config,
            logger=logger,
            ai_tool="iflow"
        )

        # 设置一些统计值
        handler.error_count = 10
        handler.fix_success_count = 7
        handler.fix_failure_count = 3
        handler.restart_count = 2

        # 获取统计信息
        stats = handler.get_statistics()

        # 验证统计信息
        assert stats["error_count"] == 10
        assert stats["fix_success_count"] == 7
        assert stats["fix_failure_count"] == 3
        assert stats["restart_count"] == 2
        assert stats["fix_success_rate"] == 70.0

        print("  ✓ 统计信息获取成功")


def test_print_statistics():
    """测试打印统计信息"""
    print("测试打印统计信息...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建模拟配置和日志
        config = MagicMock()
        logger = MagicMock()

        # 初始化错误处理器
        handler = UnifiedErrorHandler(
            project_root=temp_path,
            config=config,
            logger=logger,
            ai_tool="iflow"
        )

        # 设置一些统计值
        handler.error_count = 5
        handler.fix_success_count = 3
        handler.fix_failure_count = 2
        handler.restart_count = 1

        # 打印统计信息
        handler.print_statistics()

        # 验证日志调用
        assert logger.info.call_count >= 5  # 至少调用5次（包括分隔符）

        print("  ✓ 统计信息打印成功")


def test_analyze_error_with_exception():
    """测试错误分析功能"""
    print("测试错误分析功能...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建模拟配置和日志
        config = MagicMock()
        logger = MagicMock()

        # 初始化错误处理器
        handler = UnifiedErrorHandler(
            project_root=temp_path,
            config=config,
            logger=logger,
            ai_tool="iflow"
        )

        # 模拟一个错误
        error = ValueError("测试错误")
        context = {"session": 1}

        # 分析错误
        analysis = handler._analyze_error(error, context)

        # 验证分析结果
        assert "error_type" in analysis
        assert "error_message" in analysis
        assert "error_analysis" in analysis

        print("  ✓ 错误分析功能成功")


def test_analyze_error_with_fallback():
    """测试错误分析失败时的回退"""
    print("测试错误分析失败时的回退...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建模拟配置和日志
        config = MagicMock()
        logger = MagicMock()

        # 初始化错误处理器
        handler = UnifiedErrorHandler(
            project_root=temp_path,
            config=config,
            logger=logger,
            ai_tool="iflow"
        )

        # Mock 错误分析器抛出异常
        handler.error_analyzer.analyze_error = MagicMock(side_effect=Exception("分析失败"))

        # 模拟一个错误
        error = ValueError("测试错误")
        context = {"session": 1}

        # 分析错误
        analysis = handler._analyze_error(error, context)

        # 验证回退结果
        assert analysis["error_type"] == "ValueError"
        assert analysis["error_message"] == "测试错误"
        assert analysis["error_analysis"]["severity"] == "medium"

        print("  ✓ 错误分析回退功能成功")


async def test_handle_error_with_continue_callback():
    """测试带继续回调的错误处理"""
    print("测试带继续回调的错误处理...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 创建模拟配置和日志
        config = MagicMock()
        config.get_auto_restart_enabled = MagicMock(return_value=True)
        logger = MagicMock()

        # 初始化错误处理器
        handler = UnifiedErrorHandler(
            project_root=temp_path,
            config=config,
            logger=logger,
            ai_tool="iflow"
        )

        # 模拟一个简单的错误
        error = ValueError("测试错误")

        # 创建继续回调
        continue_callback = AsyncMock()

        # Mock 错误分析和自动修复
        handler._analyze_error = MagicMock(return_value={
            "error_type": "ValueError",
            "error_message": "测试错误",
            "error_analysis": {
                "severity": "medium",
                "description": "测试错误描述"
            },
            "suggested_fixes": []
        })
        handler._attempt_auto_fix = AsyncMock(return_value=True)
        handler._save_crash_info = MagicMock(return_value=temp_path / "crash_test.json")
        handler.restart_manager = MagicMock()
        handler.restart_manager.analyze_restart_strategy = MagicMock(return_value={
            "should_restart": False,
            "reason": "修复成功，无需重启"
        })

        # 处理错误
        result = await handler.handle_error(error, continue_callback=continue_callback)

        # 验证结果
        assert result is True
        assert continue_callback.called  # 回调应该被调用

        print("  ✓ 带继续回调的错误处理成功")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("运行统一错误处理器测试")
    print("=" * 60)
    print()

    # 同步测试
    test_unified_error_handler_initialization()
    print()
    test_save_crash_info()
    print()
    test_get_statistics()
    print()
    test_print_statistics()
    print()
    test_analyze_error_with_exception()
    print()
    test_analyze_error_with_fallback()
    print()

    # 异步测试
    asyncio.run(test_handle_error_with_auto_fix_enabled())
    print()
    asyncio.run(test_handle_error_with_auto_fix_disabled())
    print()
    asyncio.run(test_handle_error_with_fix_failure())
    print()
    asyncio.run(test_handle_error_with_continue_callback())
    print()

    print("=" * 60)
    print("所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()