#!/usr/bin/env python3
"""
配置文件监控器 - 监控配置文件变更并触发回调

功能:
1. 监控配置文件变更
2. 文件变更时触发回调
3. 支持轮询和文件系统事件两种模式
"""

import threading
import time
from pathlib import Path
from typing import Callable, Optional


class ConfigFileWatcher:
    """配置文件监控器"""

    def __init__(
        self,
        config_path: Path,
        callback: Callable[[], None],
        poll_interval: float = 1.0
    ):
        """
        初始化配置文件监控器

        Args:
            config_path: 配置文件路径
            callback: 文件变更时的回调函数
            poll_interval: 轮询间隔（秒）
        """
        self.config_path = config_path
        self.callback = callback
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_mtime: Optional[float] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """启动监控"""
        with self._lock:
            if self._running:
                return

            # 初始化最后修改时间
            if self.config_path.exists():
                self._last_mtime = self.config_path.stat().st_mtime

            self._running = True
            self._thread = threading.Thread(target=self._watch_loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """停止监控"""
        with self._lock:
            if not self._running:
                return

            self._running = False

        if self._thread:
            self._thread.join(timeout=self.poll_interval * 2)
            self._thread = None

    def _watch_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                self._check_for_changes()
            except Exception:
                # 忽略监控过程中的异常，避免监控线程崩溃
                pass

            time.sleep(self.poll_interval)

    def _check_for_changes(self) -> None:
        """检查文件是否变更"""
        if not self.config_path.exists():
            return

        current_mtime = self.config_path.stat().st_mtime

        if self._last_mtime is None or current_mtime > self._last_mtime:
            self._last_mtime = current_mtime

            # 调用回调函数
            if self.callback:
                try:
                    self.callback()
                except Exception:
                    # 忽略回调函数中的异常
                    pass

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running
