#!/usr/bin/env python3
"""
AI 守护监控进程

专门用于监视 AI 循环进程，实现平级架构
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

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.ipc import IPCManager
from dev_bot.output_router import (
    get_output_router,
    OutputSource,
    LogLevel
)
from dev_bot.anomaly_detector import (
    get_anomaly_detector,
    AnomalyType,
    AnomalySeverity
)


class AIGuardianMonitor:
    """AI 守护监控器

    专门监视 AI 循环进程的健康状态
    """

    def __init__(self, project_root: Path, check_interval: int = 10):
        self.project_root = project_root
        self.check_interval = check_interval
        self.ipc = IPCManager(project_root)
        self.output_router = get_output_router()

        # 异常检测器
        self.anomaly_detector = get_anomaly_detector(project_root)

        self.is_running = False
        self.ai_loop_process: Optional[subprocess.Popen] = None
        self.ai_loop_pid: Optional[int] = None

        # 健康状态
        self.ai_loop_healthy = True
        self.last_check_time = 0
        self.last_heartbeat_time = 0

        # 重启统计
        self.restart_count = 0
        self.max_restarts = 10

        # 启动命令
        self.ai_loop_startup_command = [
            sys.executable,
            str(project_root / "dev_bot" / "ai_loop_process.py"),
            str(project_root),
            "config.json"
        ]

        # 注册信号处理
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)

    async def start(self):
        """启动守护监控"""
        self.is_running = True

        await self.output_router.emit_guardian(
            LogLevel.INFO,
            f"启动 AI 守护监控（PID: {os.getpid()}）"
        )

        # 启动异常检测器
        await self.anomaly_detector.start()

        # 启动 AI 循环进程
        await self._start_ai_loop()

        # 启动监控循环
        asyncio.create_task(self._monitor_loop())

        # 启动心跳检查
        asyncio.create_task(self._heartbeat_check())

        await self.output_router.emit_guardian(
            LogLevel.SUCCESS,
            "AI 守护监控已启动"
        )

    async def stop(self):
        """停止守护监控"""
        self.is_running = False

        await self.output_router.emit_guardian(
            LogLevel.INFO,
            "停止 AI 守护监控"
        )

        # 停止异常检测器
        await self.anomaly_detector.stop()

        # 停止 AI 循环
        if self.ai_loop_process:
            await self._stop_ai_loop()

        await self.output_router.emit_guardian(
            LogLevel.SUCCESS,
            "AI 守护监控已停止"
        )

    async def _start_ai_loop(self):
        """启动 AI 循环进程"""
        await self.output_router.emit_guardian(
            LogLevel.INFO,
            f"启动 AI 循环进程: {' '.join(self.ai_loop_startup_command)}"
        )

        try:
            # 检查重启次数
            if self.restart_count >= self.max_restarts:
                await self.output_router.emit_guardian(
                    LogLevel.ERROR,
                    f"AI 循环重启次数已达上限（{self.max_restarts}），停止尝试"
                )
                return False

            # 启动进程
            process = subprocess.Popen(
                self.ai_loop_startup_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            self.ai_loop_process = process
            self.ai_loop_pid = process.pid

            # 更新心跳时间
            self.last_heartbeat_time = time.time()

            # 启动输出捕获
            asyncio.create_task(self._capture_ai_loop_output())

            await self.output_router.emit_guardian(
                LogLevel.SUCCESS,
                f"AI 循环进程已启动（PID: {self.ai_loop_pid}，第 {self.restart_count + 1} 次）"
            )

            return True

        except Exception as e:
            await self.output_router.emit_guardian(
                LogLevel.ERROR,
                f"启动 AI 循环进程失败: {e}"
            )
            return False

    async def _stop_ai_loop(self):
        """停止 AI 循环进程"""
        if not self.ai_loop_process:
            return

        await self.output_router.emit_guardian(
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

            await self.output_router.emit_guardian(
                LogLevel.SUCCESS,
                "AI 循环进程已停止"
            )

        except Exception as e:
            await self.output_router.emit_guardian(
                LogLevel.ERROR,
                f"停止 AI 循环进程失败: {e}"
            )

        self.ai_loop_process = None
        self.ai_loop_pid = None

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

                    text = line.decode('utf-8', errors='ignore').strip()
                    if text:
                        await self.output_router.emit_ai_loop(level, text)
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
            await self._check_ai_loop_health()
            await asyncio.sleep(self.check_interval)

    async def _heartbeat_check(self):
        """心跳检查"""
        while self.is_running:
            # 检查 AI 循环是否在更新状态文件
            status = self.ipc.read_status("ai_loop")
            if status:
                last_seen = status.get("last_seen")
                if last_seen:
                    self.last_heartbeat_time = last_seen

            # 检查心跳超时
            if time.time() - self.last_heartbeat_time > 60:
                await self.output_router.emit_guardian(
                    LogLevel.WARNING,
                    f"AI 循环心跳超时（最后心跳: {self.last_heartbeat_time}）"
                )
                self.ai_loop_healthy = False

            await asyncio.sleep(5)

    async def _check_ai_loop_health(self):
        """检查 AI 循环健康状态"""
        if not self.ai_loop_pid:
            return

        self.last_check_time = time.time()

        # 检查进程是否存在
        try:
            os.kill(self.ai_loop_pid, 0)
            self.ai_loop_healthy = True
        except OSError:
            self.ai_loop_healthy = False

            await self.output_router.emit_guardian(
                LogLevel.ERROR,
                f"AI 循环进程（PID: {self.ai_loop_pid}）已停止"
            )

            # 尝试重启
            if self.is_running:
                await self._restart_ai_loop()

    async def _restart_ai_loop(self):
        """重启 AI 循环"""
        await self.output_router.emit_guardian(
            LogLevel.WARNING,
            "尝试重启 AI 循环..."
        )

        # 等待一段时间
        await asyncio.sleep(2)

        # 停止旧进程
        if self.ai_loop_process:
            try:
                self.ai_loop_process.kill()
                self.ai_loop_process.wait(timeout=5)
            except:
                pass

        # 增加重启计数
        self.restart_count += 1

        # 启动新进程
        success = await self._start_ai_loop()

        if success:
            await self.output_router.emit_guardian(
                LogLevel.SUCCESS,
                f"AI 循环重启成功（第 {self.restart_count} 次）"
            )
        else:
            await self.output_router.emit_guardian(
                LogLevel.ERROR,
                f"AI 循环重启失败（第 {self.restart_count} 次）"
            )

    def _handle_sigterm(self, signum, frame):
        """处理 SIGTERM 信号"""
        asyncio.create_task(self.stop())

    def _handle_sigint(self, signum, frame):
        """处理 SIGINT 信号"""
        asyncio.create_task(self.stop())

    async def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        anomaly_stats = await self.anomaly_detector.get_stats()

        return {
            "is_running": self.is_running,
            "ai_loop": {
                "pid": self.ai_loop_pid,
                "healthy": self.ai_loop_healthy,
                "restart_count": self.restart_count,
                "max_restarts": self.max_restarts,
                "last_check": self.last_check_time,
                "last_heartbeat": self.last_heartbeat_time
            },
            "anomalies": anomaly_stats
        }


async def main():
    """主函数"""
    project_root = Path.cwd()

    monitor = AIGuardianMonitor(project_root, check_interval=10)

    # 启动监控
    await monitor.start()

    # 写入状态
    monitor.ipc.write_status("guardian", {
        "status": "running",
        "pid": os.getpid(),
        "ai_loop_pid": monitor.ai_loop_pid
    })

    # 保持运行
    try:
        while monitor.is_running:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())