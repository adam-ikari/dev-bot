#!/usr/bin/env python3
"""
REPL 模式用户输入管理器
允许用户在 AI 开发循环中输入指令，但不阻塞主循环
"""

import queue
import threading
import time
from typing import Callable, Dict, List, Optional


class UserInputManager:
    """用户输入管理器"""

    def __init__(self):
        self.input_queue: queue.Queue = queue.Queue()
        self.input_history: List[str] = []
        self.max_history = 100
        self.is_running = False
        self.input_thread: Optional[threading.Thread] = None
        self.pending_inputs: List[str] = []
        self.command_handlers: Dict[str, Callable] = {}  # 命令处理器映射

        # 注册内置命令
        self._register_builtin_commands()

    def _register_builtin_commands(self):
        """注册内置命令"""
        self.command_handlers = {
            'help': self._cmd_help,
            'history': self._cmd_history,
            'clear': self._cmd_clear,
            'exit': self._cmd_exit,
            'quit': self._cmd_exit,
        }

    def register_command(self, command: str, handler: Callable):
        """注册自定义命令处理器"""
        self.command_handlers[command] = handler

    def _cmd_help(self, args: List[str]) -> str:
        """显示帮助信息"""
        help_text = "可用命令:\n"
        for cmd in sorted(self.command_handlers.keys()):
            help_text += f"  {cmd}\n"
        return help_text

    def _cmd_history(self, args: List[str]) -> str:
        """显示输入历史"""
        count = int(args[0]) if args and args[0].isdigit() else 10
        recent = self.get_recent_inputs(count)
        if not recent:
            return "没有输入历史"
        return "\n".join(f"{i+1}. {inp}" for i, inp in enumerate(recent))

    def _cmd_clear(self, args: List[str]) -> str:
        """清空输入历史"""
        self.input_history.clear()
        return "输入历史已清空"

    def _cmd_exit(self, args: List[str]) -> str:
        """退出命令"""
        return "退出命令已接收"

    def process_input(self, input_text: str) -> Optional[str]:
        """
        处理用户输入

        Returns:
            处理结果，如果不是命令则返回 None
        """
        if not input_text or not input_text.strip():
            return None

        input_text = input_text.strip()

        # 检查是否是命令（以 / 开头）
        if input_text.startswith('/'):
            parts = input_text[1:].split()
            if not parts:
                return "无效的命令"

            command = parts[0].lower()
            args = parts[1:]

            if command in self.command_handlers:
                try:
                    return self.command_handlers[command](args)
                except Exception as e:
                    return f"命令执行错误: {e}"
            else:
                return f"未知命令: {command} (使用 /help 查看可用命令)"

        return None

    def start(self):
        """启动输入监听线程"""
        if self.is_running:
            return

        self.is_running = True
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()

    def stop(self):
        """停止输入监听"""
        self.is_running = False
        if self.input_thread:
            self.input_thread.join(timeout=1)

    def _input_loop(self):
        """输入循环（后台线程）"""
        import sys

        while self.is_running:
            try:
                # 尝试使用 select 进行非阻塞读取
                import select

                # 检查是否有输入可用
                if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                    line = sys.stdin.readline()
                    if line:
                        line = line.strip()
                        if line:
                            self.input_queue.put(line)
                            self.input_history.append(line)
                            if len(self.input_history) > self.max_history:
                                self.input_history.pop(0)
                            self.pending_inputs.append(line)
            except ImportError:
                # select 不可用，跳过
                time.sleep(0.1)
            except OSError:
                # stdin 不可用，跳过
                time.sleep(0.1)
            except Exception:
                # 其他错误，记录并继续
                time.sleep(0.1)

    def get_pending_inputs(self) -> List[str]:
        """获取待处理的用户输入"""
        if not self.pending_inputs:
            return []

        result = list(self.pending_inputs)
        self.pending_inputs.clear()
        return result

    def get_recent_inputs(self, count: int = 5) -> List[str]:
        """获取最近的用户输入"""
        if not self.input_history:
            return []

        start_idx = max(0, len(self.input_history) - count)
        return self.input_history[start_idx:]


def get_user_input_manager() -> UserInputManager:
    """获取用户输入管理器实例"""
    return UserInputManager()
