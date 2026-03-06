"""
自动重启管理模块

功能：
1. 记录启动命令和环境信息
2. 检测崩溃和异常退出
3. 使用 AI 分析重启策略
4. 自动执行重启
5. 记录重启历史
"""

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class AutoRestartManager:
    """自动重启管理器"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.cache_dir = self.project_root / ".dev-bot-cache"
        self.restart_info_file = self.cache_dir / "restart_info.json"
        self.restart_history_file = self.cache_dir / "restart_history.json"
        self.crash_log_dir = self.project_root / ".crash-logs"

        # 确保目录存在
        self.cache_dir.mkdir(exist_ok=True)
        self.crash_log_dir.mkdir(exist_ok=True)

        # 加载重启历史
        self.restart_history = self._load_restart_history()

    def record_startup(self, command: str, args: List[str]) -> Dict[str, Any]:
        """记录启动信息"""
        # 分析启动参数
        parsed_args = self._analyze_startup_args(args)

        restart_info = {
            "command": command,
            "args": args,
            "args_analysis": parsed_args,
            "working_directory": str(self.project_root),
            "python_version": sys.version,
            "platform": sys.platform,
            "environment": dict(os.environ),
            "startup_time": datetime.now().isoformat(),
            "pid": os.getpid(),
            "restart_count": self._get_restart_count() + 1,
            "session_counter": self._load_session_counter()
        }

        # 保存重启信息
        with open(self.restart_info_file, 'w', encoding='utf-8') as f:
            json.dump(restart_info, f, indent=2, ensure_ascii=False)

        print_status("info", f"已记录启动信息（重启次数: {restart_info['restart_count']}）")
        print_status("info", f"启动参数分析: {parsed_args['summary']}")
        return restart_info

    def _analyze_startup_args(self, args: List[str]) -> Dict[str, Any]:
        """分析启动参数"""
        analysis = {
            "has_project_path": False,
            "project_path": None,
            "has_mode": False,
            "mode": None,
            "flags": [],
            "unknown_args": [],
            "summary": ""
        }

        i = 0
        while i < len(args):
            arg = args[i]

            # 检查项目路径参数
            if arg in ['--project-path', '-p']:
                if i + 1 < len(args):
                    analysis['has_project_path'] = True
                    analysis['project_path'] = args[i + 1]
                    i += 1
            # 检查模式参数
            elif arg in ['--mode', '-m']:
                if i + 1 < len(args):
                    analysis['has_mode'] = True
                    analysis['mode'] = args[i + 1]
                    i += 1
            # 检查标志参数
            elif arg.startswith('--no-'):
                analysis['flags'].append(arg)
            elif arg.startswith('--'):
                analysis['unknown_args'].append(arg)

            i += 1

        # 生成摘要
        summary_parts = []
        if analysis['has_project_path']:
            summary_parts.append(f"项目: {analysis['project_path']}")
        if analysis['has_mode']:
            summary_parts.append(f"模式: {analysis['mode']}")
        if analysis['flags']:
            summary_parts.append(f"禁用: {', '.join(analysis['flags'])}")

        analysis['summary'] = ', '.join(summary_parts) if summary_parts else '默认配置'

        return analysis

    def record_crash(self, error_type: str, error_message: str, traceback: str = "") -> Path:
        """记录崩溃信息"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_log = self.crash_log_dir / f"crash_{timestamp}.log"

        crash_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "traceback": traceback,
            "restart_info": self._load_restart_info() if self.restart_info_file.exists() else None
        }

        with open(crash_log, 'w', encoding='utf-8') as f:
            json.dump(crash_info, f, indent=2, ensure_ascii=False)

        print_status("error", f"已记录崩溃日志: {crash_log}")
        return crash_log

    def analyze_restart_strategy(
        self,
        crash_log: Path,
        ai_command: str = "iflow",
    ) -> Dict[str, Any]:
        """使用 AI 分析重启策略（主要方法）"""
        print_status("info", "正在使用 AI 分析重启策略...")

        # 读取崩溃日志
        with open(crash_log, encoding='utf-8') as f:
            crash_info = json.load(f)

        restart_info = crash_info.get('restart_info', {})

        # 获取启动参数分析
        args_analysis = restart_info.get('args_analysis', {}) if restart_info else {}

        # 构建 AI 提示 - 让 AI 成为主要决策者
        prompt = f"""你是 Dev-Bot 的重启策略分析师。请基于以下信息分析是否应该重启以及如何重启：

=== 崩溃信息 ===
- 时间: {crash_info['timestamp']}
- 错误类型: {crash_info['error_type']}
- 错误消息: {crash_info['error_message']}
- 堆栈跟踪:
{crash_info.get('traceback', 'N/A')}

=== 启动信息 ===
- 命令: {restart_info.get('command', 'N/A') if restart_info else 'N/A'}
- 原始参数: {restart_info.get('args', []) if restart_info else []}
- 启动参数分析: {args_analysis.get('summary', 'N/A') if args_analysis else 'N/A'}
- 项目路径: {args_analysis.get('project_path', 'N/A') if args_analysis else 'N/A'}
- 运行模式: {args_analysis.get('mode', 'N/A') if args_analysis else 'N/A'}
- 禁用的功能: {args_analysis.get('flags', []) if args_analysis else []}
- 重启次数: {restart_info.get('restart_count', 0) if restart_info else 0}

=== 分析要求 ===
请基于启动命令和崩溃信息，智能决定重启策略。考虑以下因素：

1. 启动参数是否可能导致崩溃？
   - 某些模式可能不适合当前情况
   - 某些禁用的标志可能导致问题
   - 项目路径是否有问题

2. 崩溃原因是否可以通过修改参数解决？
   - 超时 → 是否需要禁用自动修复或切换模式？
   - 内存不足 → 是否需要减少功能？
   - 依赖问题 → 是否需要先分析依赖？
   - 网络问题 → 是否需要延迟重启？

3. 重启次数是否过多？
   - 如果已经重启多次，是否应该停止？

4. 是否需要人工干预？
   - 认证问题、权限问题、配置问题

=== 重启策略 ===
请以 JSON 格式返回你的分析和决策：

{{
  "analysis": "对崩溃原因和启动参数的详细分析",
  "should_restart": true/false,
  "restart_strategy": "immediate|delayed|modified|manual",
  "delay_seconds": 5,
  "modified_args": ["--mode", "analyze", "--no-auto-fix"],
  "keep_original_args": true/false,
  "reason": "重启策略的原因",
  "recommendation": "详细建议",
  "risk_assessment": "低/中/高"
}}

重启策略说明：
- immediate: 立即重启
- delayed: 延迟重启（delay_seconds 秒后）
- modified: 修改参数后重启（modified_args 指定要修改的参数）
- manual: 需要人工干预，不自动重启

注意事项：
- modified策略：keep_original_args为true时保留原始参数并添加新参数，false时完全替换
- 修改参数时应考虑参数依赖关系
- 关键错误（认证、权限、配置）应返回manual策略

只返回 JSON，不要有任何其他文字。
"""

        try:
            # 调用 AI 工具分析
            result = subprocess.run(
                [ai_command],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=90  # 增加超时时间，给 AI 更多思考时间
            )

            if result.returncode == 0:
                # 尝试解析 JSON
                analysis = self._extract_json_from_output(result.stdout)
                if analysis:
                    # 记录 AI 分析结果
                    self._log_ai_analysis(prompt, result.stdout, analysis)
                    return analysis

            # AI 分析失败，使用默认策略
            return self._get_default_restart_strategy(crash_info)

        except Exception as e:
            print_status("warning", f"AI 分析失败: {e}，使用默认策略")
            return self._get_default_restart_strategy(crash_info)

    def _log_ai_analysis(self, prompt: str, ai_output: str, analysis: Dict[str, Any]):
        """记录 AI 分析结果"""
        ai_analysis_log = self.cache_dir / "ai_restart_analysis.log"

        with open(ai_analysis_log, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write("\n=== AI Prompt ===\n")
            f.write(prompt)
            f.write("\n\n=== AI Output ===\n")
            f.write(ai_output)
            f.write("\n\n=== Parsed Analysis ===\n")
            f.write(json.dumps(analysis, indent=2, ensure_ascii=False))
            f.write(f"\n{'='*80}\n")

    def analyze_restart_strategy_by_args(
        self,
        crash_log: Path,
        ai_command: str = "iflow",
    ) -> Dict[str, Any]:
        """基于启动参数分析重启策略"""
        print_status("info", "正在分析启动参数并生成重启策略...")

        # 读取崩溃日志
        with open(crash_log, encoding='utf-8') as f:
            crash_info = json.load(f)

        restart_info = crash_info.get('restart_info', {})
        if not restart_info:
            return self._get_default_restart_strategy(crash_info)

        args_analysis = restart_info.get('args_analysis', {})

        # 根据启动参数分析崩溃原因并制定策略
        strategy = {
            "should_restart": True,
            "restart_strategy": "delayed",
            "delay_seconds": 5,
            "modified_args": [],
            "reason": "",
            "recommendation": ""
        }

        crash_info.get('error_type', '').lower()
        error_message = crash_info.get('error_message', '').lower()

        # 策略 1: 检查重启次数，防止无限重启
        restart_count = restart_info.get('restart_count', 0)
        if restart_count >= 3:
            return {
                "should_restart": False,
                "restart_strategy": "manual",
                "reason": f"已重启 {restart_count} 次，防止无限重启",
                "recommendation": "请检查根本原因并修复后再启动"
            }

        # 策略 2: 检查是否是关键错误（认证、权限等）
        critical_keywords = [
            '登录', '认证', '权限', 'api key',
            'invalid', 'unauthorized', 'forbidden'
        ]
        if any(keyword in error_message.lower() for keyword in critical_keywords):
            return {
                "should_restart": False,
                "restart_strategy": "manual",
                "reason": "检测到需要人工干预的关键错误",
                "recommendation": "请检查认证信息和权限设置"
            }

        # 其他情况由 AI 决定
        return {
            "should_restart": True,
            "restart_strategy": "delayed",
            "delay_seconds": 5,
            "modified_args": [],
            "reason": "检测到可恢复的错误，由 AI 决定重启策略",
            "recommendation": "等待 AI 分析结果"
        }

        # 记录分析结果
        analysis_log = self.cache_dir / "restart_strategy_analysis.log"
        with open(analysis_log, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write(f"启动参数分析: {args_analysis.get('summary', 'N/A')}\n")
            f.write(f"错误类型: {crash_info.get('error_type', 'N/A')}\n")
            f.write(f"错误消息: {crash_info.get('error_message', 'N/A')}\n")
            f.write(f"重启策略: {strategy.get('restart_strategy', 'unknown')}\n")
            f.write(f"重启原因: {strategy.get('reason', 'N/A')}\n")
            f.write(f"建议: {strategy.get('recommendation', 'N/A')}\n")
            f.write(f"{'='*60}\n")

        return strategy

    def execute_restart(self, restart_info: Dict[str, Any], strategy: Dict[str, Any]) -> bool:
        """执行重启"""
        if not strategy.get("should_restart", False):
            print_status("info", f"不建议自动重启: {strategy.get('reason', '未知原因')}")
            print_status("info", f"建议: {strategy.get('recommendation', '')}")
            return False

        restart_strategy = strategy.get("restart_strategy", "immediate")
        risk_assessment = strategy.get("risk_assessment", "中")

        # 打印风险评估
        print_status("info", f"风险评估: {risk_assessment}")

        # 记录重启历史
        self._record_restart_history(restart_info, strategy)

        if restart_strategy == "manual":
            print_status("info", f"需要人工干预: {strategy.get('recommendation', '请手动检查')}")
            return False

        # 延迟重启
        if restart_strategy == "delayed":
            delay = strategy.get("delay_seconds", 5)
            print_status("info", f"将在 {delay} 秒后重启...")
            time.sleep(delay)

        # 构建重启命令
        command = restart_info["command"]
        original_args = restart_info["args"]

        # 处理修改的参数
        if restart_strategy == "modified":
            modified_args = strategy.get("modified_args", [])
            keep_original = strategy.get("keep_original_args", True)

            if modified_args:
                if keep_original:
                    # 保留原始参数并添加新参数
                    args = original_args + modified_args
                    print_status("info", "使用修改后的参数重启（保留原始参数）:")
                    print_status("info", f"  原始: {' '.join(original_args)}")
                    print_status("info", f"  添加: {' '.join(modified_args)}")
                else:
                    # 完全替换参数
                    args = modified_args
                    print_status("info", "使用修改后的参数重启（替换原始参数）:")
                    print_status("info", f"  原始: {' '.join(original_args)}")
                    print_status("info", f"  新参数: {' '.join(modified_args)}")
            else:
                # 没有修改参数，使用原始参数
                args = original_args
                print_status("info", "使用原始参数重启")
        else:
            # 使用原始参数
            args = original_args

        # 执行重启
        try:
            print_status("info", f"正在重启: {command} {' '.join(args)}")

            # 记录重启日志
            self._log_restart(command, args, strategy)

            # 额外安全检查：确保所有参数都是字符串且不包含空格注入
            safe_args = []
            for arg in args:
                if not isinstance(arg, str):
                    raise ValueError(f"参数必须是字符串类型: {type(arg)}")
                # 检查参数长度防止缓冲区溢出
                if len(arg) > 4096:
                    raise ValueError(f"参数过长: {len(arg)} 字符")
                safe_args.append(arg)

            # 使用 subprocess 替换当前进程（使用列表形式避免 shell 注入）
            os.execvp(command, [command] + safe_args)

        except Exception as e:
            print_status("error", f"重启失败: {e}")
            self._record_restart_failure(str(e))
            return False

        return True

    def _load_restart_info(self) -> Optional[Dict[str, Any]]:
        """加载重启信息"""
        if self.restart_info_file.exists():
            with open(self.restart_info_file, encoding='utf-8') as f:
                return json.load(f)
        return None

    def _load_restart_history(self) -> List[Dict[str, Any]]:
        """加载重启历史"""
        if self.restart_history_file.exists():
            with open(self.restart_history_file, encoding='utf-8') as f:
                return json.load(f)
        return []

    def _record_restart_history(self, restart_info: Dict[str, Any], strategy: Dict[str, Any]):
        """记录重启历史"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "restart_count": restart_info.get("restart_count", 0),
            "strategy": strategy,
            "pid": os.getpid()
        }

        self.restart_history.append(history_entry)

        # 只保留最近 50 条记录
        if len(self.restart_history) > 50:
            self.restart_history = self.restart_history[-50:]

        with open(self.restart_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.restart_history, f, indent=2, ensure_ascii=False)

    def _get_restart_count(self) -> int:
        """获取重启次数"""
        restart_info = self._load_restart_info()
        return restart_info.get("restart_count", 0) if restart_info else 0

    def _load_session_counter(self) -> int:
        """加载会话计数器"""
        session_counter_file = self.project_root / ".ai-logs" / "session_counter.json"
        if session_counter_file.exists():
            with open(session_counter_file, encoding='utf-8') as f:
                data = json.load(f)
                return data.get("counter", 0)
        return 0

    def _get_default_restart_strategy(self, crash_info: Dict[str, Any]) -> Dict[str, Any]:
        """获取默认重启策略"""
        error_msg = crash_info.get("error_message", "").lower()

        # 检查是否需要人工干预
        critical_keywords = [
            "登录",
            "认证",
            "权限",
            "api key",
            "invalid",
            "unauthorized",
            "forbidden",
        ]
        if any(keyword in error_msg.lower() for keyword in critical_keywords):
            return {
                "should_restart": False,
                "restart_strategy": "manual",
                "reason": "检测到需要人工干预的关键错误",
                "recommendation": "请检查认证信息和权限设置",
            }

        # 检查重启次数，防止无限重启
        restart_count = self._get_restart_count()
        if restart_count >= 3:
            return {
                "should_restart": False,
                "restart_strategy": "manual",
                "reason": f"已重启 {restart_count} 次，防止无限重启",
                "recommendation": "请检查根本原因并修复后再启动"
            }

        # 默认策略：延迟重启
        return {
            "should_restart": True,
            "restart_strategy": "delayed",
            "delay_seconds": 5,
            "reason": "检测到可恢复的错误，自动重启",
            "recommendation": "如果问题持续，请检查日志"
        }

    def _extract_json_from_output(self, output: str) -> Optional[Dict[str, Any]]:
        """从 AI 输出中提取 JSON"""
        import re

        # 尝试匹配 JSON 对象
        json_match = re.search(r'\{[^{}]*"[^"]+"\s*:\s*[^{}]*\}', output)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return None

    def _log_restart(self, command: str, args: List[str], strategy: Dict[str, Any]):
        """记录重启日志"""
        restart_log = self.cache_dir / "restart.log"

        with open(restart_log, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"重启时间: {datetime.now().isoformat()}\n")
            f.write(f"命令: {command}\n")
            f.write(f"参数: {' '.join(args)}\n")
            f.write(f"策略: {strategy.get('restart_strategy', 'unknown')}\n")
            f.write(f"原因: {strategy.get('reason', 'N/A')}\n")
            f.write(f"{'='*60}\n")

    def _record_restart_failure(self, error: str):
        """记录重启失败"""
        failure_log = self.cache_dir / "restart_failures.log"

        with open(failure_log, 'a', encoding='utf-8') as f:
            f.write(f"\n{datetime.now().isoformat()} - 重启失败: {error}\n")


def print_status(status: str, message: str):
    """打印状态信息"""
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    icon = icons.get(status, "•")
    print(f"[{icon}] {message}")


def setup_crash_handlers(restart_manager: AutoRestartManager):
    """设置崩溃处理器"""

    def handle_exception(exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        import traceback

        error_type = exc_type.__name__
        error_message = str(exc_value)
        traceback_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        print_status("error", f"未捕获的异常: {error_type}: {error_message}")

        # 记录崩溃
        crash_log = restart_manager.record_crash(error_type, error_message, traceback_str)

        # 使用 AI 分析重启策略
        restart_info = restart_manager._load_restart_info()
        if restart_info:
            print_status("info", "正在使用 AI 分析重启策略...")
            strategy = restart_manager.analyze_restart_strategy(crash_log)

            # 执行重启
            if strategy.get("should_restart", False):
                restart_manager.execute_restart(restart_info, strategy)

        sys.exit(1)

    def handle_signal(signum, frame):
        """处理信号"""
        signal_name = signal.Signals(signum).name
        print_status("warning", f"收到信号: {signal_name}")

        # 记录崩溃
        crash_log = restart_manager.record_crash(
            f"Signal {signal_name}",
            f"进程被信号 {signal_name} 终止"
        )

        # 某些信号不自动重启
        if signum in [signal.SIGTERM, signal.SIGINT]:
            print_status("info", "正常退出信号，不自动重启")
            sys.exit(0)

        # 使用 AI 分析重启策略
        restart_info = restart_manager._load_restart_info()
        if restart_info:
            print_status("info", "正在使用 AI 分析重启策略...")
            strategy = restart_manager.analyze_restart_strategy(crash_log)

            # 执行重启
            if strategy.get("should_restart", False):
                restart_manager.execute_restart(restart_info, strategy)

        sys.exit(1)

    # 设置异常处理器
    sys.excepthook = handle_exception

    # 设置信号处理器
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGQUIT, handle_signal)

    print_status("success", "已设置崩溃处理器和信号处理器（AI 主导重启决策）")


# 导出快捷函数
def get_restart_manager(project_root: Optional[Path] = None) -> AutoRestartManager:
    """获取重启管理器实例"""
    return AutoRestartManager(project_root)
