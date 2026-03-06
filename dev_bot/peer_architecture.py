"""平级架构协调器

协调 AI 守护和 AI 循环的平级架构
"""
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

from dev_bot.output_router import (
    get_output_router,
    OutputSource,
    LogLevel
)
from dev_bot.ipc import IPCManager


class PeerArchitectureCoordinator:
    """平级架构协调器

    管理 AI 守护和 AI 循环的平级关系
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ipc = IPCManager(project_root)
        self.output_router = get_output_router()

        self.is_running = False
        self.guardian_process: Optional[subprocess.Popen] = None
        self.ai_loop_process: Optional[subprocess.Popen] = None

        # 进程信息
        self.guardian_pid: Optional[int] = None
        self.ai_loop_pid: Optional[int] = None

        # 健康状态
        self.guardian_healthy = True
        self.ai_loop_healthy = True

        # 最后检查时间
        self.guardian_last_check = 0
        self.ai_loop_last_check = 0

        # 注册信号处理
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)

    async def start(self):
        """启动平级架构"""
        self.is_running = True

        await self.output_router.emit_system(
            LogLevel.INFO,
            "启动平级架构协调器"
        )

        # 启动 AI 守护进程
        await self._start_guardian()

        # 启动 AI 循环进程
        await self._start_ai_loop()

        # 启动监控循环
        asyncio.create_task(self._monitor_loop())

        await self.output_router.emit_system(
            LogLevel.SUCCESS,
            "平级架构启动完成"
        )

    async def stop(self):
        """停止平级架构"""
        self.is_running = False

        await self.output_router.emit_system(
            LogLevel.INFO,
            "停止平级架构协调器"
        )

        # 停止 AI 循环
        if self.ai_loop_process:
            await self._stop_ai_loop()

        # 停止 AI 守护
        if self.guardian_process:
            await self._stop_guardian()

        await self.output_router.emit_system(
            LogLevel.SUCCESS,
            "平级架构已停止"
        )

    async def _start_guardian(self):
        """启动 AI 守护进程"""
        cmd = [
            sys.executable,
            str(self.project_root / "dev_bot" / "guardian_process.py"),
            "--check-interval", "30"
        ]

        await self.output_router.emit_system(
            LogLevel.INFO,
            f"启动 AI 守护进程: {' '.join(cmd)}"
        )

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            self.guardian_process = process
            self.guardian_pid = process.pid

            # 启动输出捕获
            asyncio.create_task(self._capture_guardian_output())

            await self.output_router.emit_system(
                LogLevel.SUCCESS,
                f"AI 守护进程已启动（PID: {self.guardian_pid}）"
            )

        except Exception as e:
            await self.output_router.emit_system(
                LogLevel.ERROR,
                f"启动 AI 守护进程失败: {e}"
            )

    async def _start_ai_loop(self):
        """启动 AI 循环进程"""
        cmd = [
            sys.executable,
            str(self.project_root / "dev_bot" / "ai_loop_process.py"),
            str(self.project_root),
            "config.json"
        ]

        await self.output_router.emit_system(
            LogLevel.INFO,
            f"启动 AI 循环进程: {' '.join(cmd)}"
        )

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            self.ai_loop_process = process
            self.ai_loop_pid = process.pid

            # 启动输出捕获
            asyncio.create_task(self._capture_ai_loop_output())

            await self.output_router.emit_system(
                LogLevel.SUCCESS,
                f"AI 循环进程已启动（PID: {self.ai_loop_pid}）"
            )

        except Exception as e:
            await self.output_router.emit_system(
                LogLevel.ERROR,
                f"启动 AI 循环进程失败: {e}"
            )

    async def _stop_guardian(self):
        """停止 AI 守护进程"""
        if not self.guardian_process:
            return

        await self.output_router.emit_system(
            LogLevel.INFO,
            f"停止 AI 守护进程（PID: {self.guardian_pid}）"
        )

        try:
            # 发送 SIGTERM
            self.guardian_process.terminate()

            # 等待进程结束
            try:
                self.guardian_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # 强制杀死
                self.guardian_process.kill()
                self.guardian_process.wait()

            await self.output_router.emit_system(
                LogLevel.SUCCESS,
                "AI 守护进程已停止"
            )

        except Exception as e:
            await self.output_router.emit_system(
                LogLevel.ERROR,
                f"停止 AI 守护进程失败: {e}"
            )

        self.guardian_process = None
        self.guardian_pid = None

    async def _stop_ai_loop(self):
        """停止 AI 循环进程"""
        if not self.ai_loop_process:
            return

        await self.output_router.emit_system(
            LogLevel.INFO,
            f"停止 AI 循环进程（PID: {self.ai_loop_pid}）"
        )

        try:
            # 发送 SIGTERM
            self.ai_loop_process.terminate()

            # 等待进程结束
            try:
                self.ai_loop_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # 强制杀死
                self.ai_loop_process.kill()
                self.ai_loop_process.wait()

            await self.output_router.emit_system(
                LogLevel.SUCCESS,
                "AI 循环进程已停止"
            )

        except Exception as e:
            await self.output_router.emit_system(
                LogLevel.ERROR,
                f"停止 AI 循环进程失败: {e}"
            )

        self.ai_loop_process = None
        self.ai_loop_pid = None

    async def _capture_guardian_output(self):
        """捕获 AI 守护输出"""
        if not self.guardian_process:
            return

        async def read_stream(stream, level: LogLevel):
            while True:
                try:
                    line = stream.readline()
                    if not line:
                        break

                    await self.output_router.emit_guardian(
                        level,
                        line.decode('utf-8', errors='ignore').strip()
                    )
                except:
                    break

        # 读取 stdout
        asyncio.create_task(
            read_stream(self.guardian_process.stdout, LogLevel.INFO)
        )

        # 读取 stderr
        asyncio.create_task(
            read_stream(self.guardian_process.stderr, LogLevel.ERROR)
        )

    async def _capture_ai_loop_output(self):
        """捕获 AI 循环输出"""
        if not self.ai_loop_process:
            return

        async def read_stream(stream, level: LogLevel):
            while True:
                try:
                    line = stream.readline()
                    if not line:
                        break

                    await self.output_router.emit_ai_loop(
                        level,
                        line.decode('utf-8', errors='ignore').strip()
                    )
                except:
                    break

        # 读取 stdout
        asyncio.create_task(
            read_stream(self.ai_loop_process.stdout, LogLevel.INFO)
        )

        # 读取 stderr
        asyncio.create_task(
            read_stream(self.ai_loop_process.stderr, LogLevel.ERROR)
        )

    async def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            await self._check_guardian_health()
            await self._check_ai_loop_health()
            await asyncio.sleep(10)

    async def _check_guardian_health(self):
        """检查 AI 守护健康状态"""
        if not self.guardian_pid:
            return

        try:
            # 检查进程是否存在
            os.kill(self.guardian_pid, 0)

            self.guardian_healthy = True
            self.guardian_last_check = time.time()

        except OSError:
            self.guardian_healthy = False

            await self.output_router.emit_system(
                LogLevel.ERROR,
                f"AI 守护进程（PID: {self.guardian_pid}）已停止"
            )

            # 尝试重启
            if self.is_running:
                await self._start_guardian()

    async def _check_ai_loop_health(self):
        """检查 AI 循环健康状态"""
        if not self.ai_loop_pid:
            return

        try:
            # 检查进程是否存在
            os.kill(self.ai_loop_pid, 0)

            self.ai_loop_healthy = True
            self.ai_loop_last_check = time.time()

        except OSError:
            self.ai_loop_healthy = False

            await self.output_router.emit_system(
                LogLevel.ERROR,
                f"AI 循环进程（PID: {self.ai_loop_pid}）已停止"
            )

            # 尝试重启
            if self.is_running:
                await self._start_ai_loop()

    def _handle_sigterm(self, signum, frame):
        """处理 SIGTERM 信号"""
        asyncio.create_task(self.stop())

    def _handle_sigint(self, signum, frame):
        """处理 SIGINT 信号"""
        asyncio.create_task(self.stop())

    async def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "is_running": self.is_running,
            "guardian": {
                "pid": self.guardian_pid,
                "healthy": self.guardian_healthy,
                "last_check": self.guardian_last_check
            },
            "ai_loop": {
                "pid": self.ai_loop_pid,
                "healthy": self.ai_loop_healthy,
                "last_check": self.ai_loop_last_check
            },
            "output_stats": await self.output_router.get_stats()
        }