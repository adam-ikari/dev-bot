#!/usr/bin/env python3
"""
统一错误处理器 - 整合 AI 自动修复和重启功能
"""

import asyncio
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from dev_bot.auto_restart import get_restart_manager
from dev_bot.core import AIOrchestrator, AutoFixer
from dev_bot.error_analyzer import ErrorAnalyzer


class UnifiedErrorHandler:
    """统一错误处理器"""

    def __init__(
        self,
        project_root: Path,
        config: Any,
        logger: Any,
        ai_tool: str = "iflow"
    ):
        """初始化错误处理器

        Args:
            project_root: 项目根目录
            config: 配置对象
            logger: 日志记录器
            ai_tool: AI 工具名称
        """
        self.project_root = project_root
        self.config = config
        self.logger = logger
        self.ai_tool = ai_tool

        # 初始化组件
        self.error_analyzer = ErrorAnalyzer(ai_tool=ai_tool)
        self.ai_orchestrator = AIOrchestrator()
        self.auto_fixer = AutoFixer(self.ai_orchestrator)
        self.restart_manager = get_restart_manager(project_root)

        # 统计信息
        self.error_count = 0
        self.fix_success_count = 0
        self.fix_failure_count = 0
        self.restart_count = 0

    async def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        continue_callback: Optional[Callable] = None
    ) -> bool:
        """统一错误处理

        Args:
            error: 异常对象
            context: 错误上下文信息
            continue_callback: 继续运行的回调函数

        Returns:
            bool: 是否应该继续运行（False 表示应该退出/重启）
        """
        self.error_count += 1

        # 构建完整的上下文
        full_context = {
            "error_count": self.error_count,
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
        }
        if context:
            full_context.update(context)

        # 记录错误
        self.logger.error(f"错误 #{self.error_count}: {type(error).__name__}: {error}")
        self.logger.debug(f"堆栈跟踪:\n{traceback.format_exc()}")

        # 检查是否启用自动修复
        if not self.config.get_auto_restart_enabled():
            self.logger.info("自动修复未启用，跳过")
            return False

        try:
            # 步骤 1: 分析错误
            self.logger.info("[步骤 1/4] 正在分析错误...")
            analysis = self._analyze_error(error, full_context)
            self.logger.info(f"错误类型: {analysis.get('error_type', 'unknown')}")
            severity = analysis.get('error_analysis', {}).get('severity', 'unknown')
            self.logger.info(f"严重程度: {severity}")

            # 步骤 2: 尝试自动修复
            self.logger.info("[步骤 2/4] 正在尝试自动修复...")
            fix_result = await self._attempt_auto_fix(error, analysis)

            if fix_result:
                self.fix_success_count += 1
                msg = f"✅ 自动修复成功（成功次数: {self.fix_success_count}/{self.error_count}）"
                self.logger.success(msg)

                # 如果有继续回调，调用它
                if continue_callback:
                    await asyncio.sleep(1)  # 给系统一点时间恢复
                    await continue_callback()

                return True
            else:
                self.fix_failure_count += 1
                msg = f"❌ 自动修复失败（失败次数: {self.fix_failure_count}/{self.error_count}）"
                self.logger.warning(msg)

            # 步骤 3: 保存崩溃信息
            self.logger.info("[步骤 3/4] 正在保存崩溃信息...")
            crash_log_file = self._save_crash_info(error, analysis, full_context)
            self.logger.info(f"崩溃信息已保存: {crash_log_file}")

            # 步骤 4: 分析重启策略
            self.logger.info("[步骤 4/4] 正在分析重启策略...")
            restart_strategy = self.restart_manager.analyze_restart_strategy(crash_log_file)

            if restart_strategy.get("should_restart", False):
                self.restart_count += 1
                reason = restart_strategy.get('reason', 'unknown')
                delay = restart_strategy.get('delay', 5)

                self.logger.warning(f"⚠️  需要重启: {reason}")
                self.logger.info(f"重启延迟: {delay}秒（重启次数: {self.restart_count}）")

                # 执行重启
                await asyncio.sleep(delay)
                self._execute_restart(restart_strategy)

                return False
            else:
                self.logger.info("✓ 不需要重启，可以继续运行")
                return True

        except Exception as handler_error:
            self.logger.error(f"❌ 错误处理器本身出错: {handler_error}")
            self.logger.debug(f"处理器错误堆栈:\n{traceback.format_exc()}")
            return False

    def _analyze_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析错误

        Args:
            error: 异常对象
            context: 上下文信息

        Returns:
            错误分析结果
        """
        try:
            analysis = self.error_analyzer.analyze_error(error, context)
            return analysis
        except Exception as e:
            self.logger.warning(f"错误分析失败: {e}")
            # 返回默认分析结果
            return {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "error_analysis": {
                    "severity": "medium",
                    "description": str(error)
                },
                "suggested_fixes": []
            }

    async def _attempt_auto_fix(self, error: Exception, analysis: Dict[str, Any]) -> bool:
        """尝试自动修复

        Args:
            error: 异常对象
            analysis: 错误分析结果

        Returns:
            bool: 修复是否成功
        """
        try:
            # 检查是否可以自动修复
            can_fix = self.error_analyzer.can_auto_fix(analysis)
            self.logger.info(f"是否可自动修复: {can_fix}")

            # 放宽条件：总是尝试修复
            if can_fix or True:
                errors = [str(error)]
                self.logger.info(f"尝试修复错误: {errors}")

                fix_result = self.auto_fixer.fix_errors(errors)
                return fix_result
            else:
                self.logger.info("跳过自动修复（条件不满足）")
                return False

        except Exception as e:
            self.logger.error(f"自动修复过程中出错: {e}")
            return False

    def _save_crash_info(
        self,
        error: Exception,
        analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Path:
        """保存崩溃信息

        Args:
            error: 异常对象
            analysis: 错误分析结果
            context: 上下文信息

        Returns:
            崩溃日志文件路径
        """
        crash_log_dir = self.project_root / ".crash-logs"
        crash_log_dir.mkdir(exist_ok=True)
        crash_log_file = crash_log_dir / f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        crash_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "session": context.get("session", 0),
            "project_root": str(self.project_root),
            "system_info": {
                "platform": sys.platform,
                "python_version": sys.version,
                "working_directory": str(Path.cwd()),
                "environment": {
                    k: v for k, v in os.environ.items()
                    if k in ['PATH', 'HOME', 'USER', 'SHELL']
                }
            },
            "auto_fix_attempted": True,
            "error_analysis": analysis,
            "context": context,
            "restart_info": {
                "command": sys.argv[0],
                "args": sys.argv[1:],
                "working_directory": str(self.project_root)
            },
            "statistics": {
                "error_count": self.error_count,
                "fix_success_count": self.fix_success_count,
                "fix_failure_count": self.fix_failure_count,
                "restart_count": self.restart_count
            }
        }

        with open(crash_log_file, 'w', encoding='utf-8') as f:
            json.dump(crash_info, f, indent=2, ensure_ascii=False)

        return crash_log_file

    def _execute_restart(self, strategy: Dict[str, Any]) -> None:
        """执行重启

        Args:
            strategy: 重启策略
        """
        restart_info = {
            "command": sys.argv[0],
            "args": sys.argv[1:]
        }

        self.logger.info("正在执行重启...")
        self.restart_manager.execute_restart(restart_info, strategy)

    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "error_count": self.error_count,
            "fix_success_count": self.fix_success_count,
            "fix_failure_count": self.fix_failure_count,
            "restart_count": self.restart_count,
            "fix_success_rate": (
                self.fix_success_count / self.error_count * 100
                if self.error_count > 0 else 0
            )
        }

    def print_statistics(self) -> None:
        """打印统计信息"""
        stats = self.get_statistics()
        self.logger.info("=" * 50)
        self.logger.info("错误处理统计:")
        self.logger.info(f"  总错误数: {stats['error_count']}")
        self.logger.info(f"  修复成功: {stats['fix_success_count']}")
        self.logger.info(f"  修复失败: {stats['fix_failure_count']}")
        self.logger.info(f"  重启次数: {stats['restart_count']}")
        self.logger.info(f"  修复成功率: {stats['fix_success_rate']:.1f}%")
        self.logger.info("=" * 50)
