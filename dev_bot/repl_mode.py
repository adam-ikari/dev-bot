#!/usr/bin/env python3

"""
REPL 模式用户输入管理器
允许用户在 AI 开发循环中输入指令，但不阻塞主循环
"""

import queue
import threading
import time
from typing import List, Optional


class UserInputManager:
    """用户输入管理器"""

    def __init__(self):
        self.input_queue: queue.Queue = queue.Queue()
        self.input_history: List[str] = []
        self.max_history = 100
        self.is_running = False
        self.input_thread: Optional[threading.Thread] = None
        self.pending_inputs: List[str] = []

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
        while self.is_running:
            try:
                # 非阻塞地尝试读取输入
                # 注意：在后台线程中使用 input() 会阻塞，所以这里使用超时
                import select
                import sys

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
            except (ImportError, OSError):
                # select.select 在某些环境下可能不可用
                time.sleep(0.1)
            except Exception:
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
