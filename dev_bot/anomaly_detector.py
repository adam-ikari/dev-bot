"""异常检测系统

检测 AI 循环的各种异常情况
"""
import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from collections import deque

from dev_bot.ipc import IPCManager
from dev_bot.output_router import (
    get_output_router,
    OutputSource,
    LogLevel
)


class AnomalyType(Enum):
    """异常类型"""
    NO_RESPONSE = "no_response"  # 无响应
    RATE_LIMIT = "rate_limit"  # 限流
    INVALID_COMMAND = "invalid_command"  # 无效指令
    INFINITE_LOOP = "infinite_loop"  # 无限循环
    MEMORY_LEAK = "memory_leak"  # 内存泄漏
    HIGH_ERROR_RATE = "high_error_rate"  # 高错误率


class AnomalySeverity(Enum):
    """异常严重程度"""
    LOW = "low"  # 低
    MEDIUM = "medium"  # 中
    HIGH = "high"  # 高
    CRITICAL = "critical"  # 严重


@dataclass
class Anomaly:
    """异常记录"""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    description: str
    detected_at: float = field(default_factory=time.time)
    details: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "anomaly_id": self.anomaly_id,
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "detected_at": self.detected_at,
            "details": self.details,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at
        }


class AnomalyDetector:
    """异常检测器

    检测 AI 循环的各种异常情况
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ipc = IPCManager(project_root)
        self.output_router = get_output_router()

        # 异常记录
        self.anomalies: Dict[str, Anomaly] = {}
        self.anomaly_counter = 0

        # 检测阈值
        self.heartbeat_timeout = 60  # 心跳超时（秒）
        self.rate_limit_threshold = 5  # 连续失败次数阈值
        self.error_rate_threshold = 0.5  # 错误率阈值
        self.command_repeat_threshold = 3  # 指令重复阈值

        # 统计数据
        self.heartbeats: Dict[str, float] = {}
        self.error_counts: Dict[str, int] = {}
        self.success_counts: Dict[str, int] = {}
        self.command_history: Dict[str, deque] = {}
        self.output_history: Dict[str, deque] = {}

        # 检测任务
        self.detection_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def start(self):
        """启动异常检测"""
        self.is_running = True
        await self.output_router.emit_guardian(
            LogLevel.INFO,
            "启动异常检测系统"
        )

        # 启动检测循环
        self.detection_task = asyncio.create_task(self._detection_loop())

    async def stop(self):
        """停止异常检测"""
        self.is_running = False

        if self.detection_task:
            self.detection_task.cancel()
            try:
                await self.detection_task
            except asyncio.CancelledError:
                pass

        await self.output_router.emit_guardian(
            LogLevel.INFO,
            "停止异常检测系统"
        )

    async def _detection_loop(self):
        """检测循环"""
        while self.is_running:
            try:
                # 检测无响应
                await self._detect_no_response()

                # 检测限流
                await self._detect_rate_limit()

                # 检测无效指令
                await self._detect_invalid_command()

                # 检测高错误率
                await self._detect_high_error_rate()

                await asyncio.sleep(10)  # 每10秒检测一次

            except Exception as e:
                await self.output_router.emit_guardian(
                    LogLevel.ERROR,
                    f"异常检测出错: {e}"
                )

    async def _detect_no_response(self):
        """检测无响应异常"""
        # 读取 AI 循环状态
        status = self.ipc.read_status("ai_loop")

        if not status:
            # 无法读取状态，可能是进程未启动
            return

        last_seen = status.get("last_seen")
        if not last_seen:
            return

        # 检查心跳超时
        elapsed = time.time() - last_seen
        if elapsed > self.heartbeat_timeout:
            # 检查是否已经记录了该异常
            anomaly_id = f"no_response_{int(time.time())}"

            if anomaly_id not in self.anomalies:
                await self._report_anomaly(
                    anomaly_id,
                    AnomalyType.NO_RESPONSE,
                    AnomalySeverity.HIGH,
                    f"AI 循环无响应（最后心跳: {last_seen}, 超时: {elapsed:.0f}秒）",
                    {
                        "last_heartbeat": last_seen,
                        "timeout": elapsed
                    }
                )

    async def _detect_rate_limit(self):
        """检测限流异常"""
        # 读取日志
        logs = self.ipc.read_logs("ai_loop", lines=100)

        # 查找限流相关错误
        rate_limit_patterns = [
            r"rate limit",
            r"429",
            r"too many requests",
            r"quota exceeded"
        ]

        recent_rate_limits = []

        for log in logs:
            for pattern in rate_limit_patterns:
                if re.search(pattern, log, re.IGNORECASE):
                    recent_rate_limits.append(log)
                    break

        # 如果连续出现多次限流错误
        if len(recent_rate_limits) >= self.rate_limit_threshold:
            anomaly_id = f"rate_limit_{int(time.time())}"

            if anomaly_id not in self.anomalies:
                await self._report_anomaly(
                    anomaly_id,
                    AnomalyType.RATE_LIMIT,
                    AnomalySeverity.HIGH,
                    f"检测到限流异常（{len(recent_rate_limits)} 次限流错误）",
                    {
                        "error_count": len(recent_rate_limits),
                        "recent_errors": recent_rate_limits[-5:]
                    }
                )

    async def _detect_invalid_command(self):
        """检测无效指令异常"""
        # 读取日志
        logs = self.ipc.read_logs("ai_loop", lines=50)

        # 查找无效指令模式
        invalid_patterns = [
            r"invalid command",
            r"unknown command",
            r"command not found",
            r"unsupported operation"
        ]

        invalid_commands = []

        for log in logs:
            for pattern in invalid_patterns:
                if re.search(pattern, log, re.IGNORECASE):
                    invalid_commands.append(log)
                    break

        # 检测重复的无效指令
        if len(invalid_commands) >= self.command_repeat_threshold:
            anomaly_id = f"invalid_command_{int(time.time())}"

            if anomaly_id not in self.anomalies:
                await self._report_anomaly(
                    anomaly_id,
                    AnomalyType.INVALID_COMMAND,
                    AnomalySeverity.MEDIUM,
                    f"检测到无效指令（{len(invalid_commands)} 次无效指令）",
                    {
                        "error_count": len(invalid_commands),
                        "recent_errors": invalid_commands[-5:]
                    }
                )

    async def _detect_high_error_rate(self):
        """检测高错误率"""
        # 读取日志
        logs = self.ipc.read_logs("ai_loop", lines=200)

        # 统计错误和成功
        error_count = 0
        success_count = 0

        for log in logs:
            if "[ERROR]" in log or "[error]" in log:
                error_count += 1
            elif "[SUCCESS]" in log or "[success]" in log:
                success_count += 1

        # 计算错误率
        total = error_count + success_count
        if total > 0:
            error_rate = error_count / total

            if error_rate > self.error_rate_threshold:
                anomaly_id = f"high_error_rate_{int(time.time())}"

                if anomaly_id not in self.anomalies:
                    await self._report_anomaly(
                        anomaly_id,
                        AnomalyType.HIGH_ERROR_RATE,
                        AnomalySeverity.MEDIUM,
                        f"检测到高错误率（错误率: {error_rate:.2%}, {error_count}/{total}）",
                        {
                            "error_rate": error_rate,
                            "error_count": error_count,
                            "success_count": success_count,
                            "total": total
                        }
                    )

    async def _report_anomaly(
        self,
        anomaly_id: str,
        anomaly_type: AnomalyType,
        severity: AnomalySeverity,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """报告异常"""
        self.anomaly_counter += 1

        anomaly = Anomaly(
            anomaly_id=anomaly_id,
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            details=details
        )

        self.anomalies[anomaly_id] = anomaly

        # 输出异常报告
        severity_symbol = {
            AnomalySeverity.LOW: "⚠️",
            AnomalySeverity.MEDIUM: "⚠️⚠️",
            AnomalySeverity.HIGH: "🚨",
            AnomalySeverity.CRITICAL: "🚨🚨"
        }.get(severity, "?")

        await self.output_router.emit_guardian(
            LogLevel.ERROR,
            f"{severity_symbol} 检测到异常: {description}"
        )

        # 保存异常记录
        await self._save_anomaly(anomaly)

    async def _save_anomaly(self, anomaly: Anomaly):
        """保存异常记录"""
        anomaly_file = self.project_root / ".ipc" / "anomalies.json"

        try:
            # 读取现有异常
            if anomaly_file.exists():
                with open(anomaly_file, 'r', encoding='utf-8') as f:
                    anomalies_data = json.load(f)
            else:
                anomalies_data = []

            # 添加新异常
            anomalies_data.append(anomaly.to_dict())

            # 只保留最近的 100 条异常
            anomalies_data = anomalies_data[-100:]

            # 保存
            with open(anomaly_file, 'w', encoding='utf-8') as f:
                json.dump(anomalies_data, f, indent=2)

        except Exception as e:
            await self.output_router.emit_guardian(
                LogLevel.ERROR,
                f"保存异常记录失败: {e}"
            )

    def record_heartbeat(self, process_type: str):
        """记录心跳"""
        self.heartbeats[process_type] = time.time()

    def record_error(self, process_type: str, error: str):
        """记录错误"""
        if process_type not in self.error_counts:
            self.error_counts[process_type] = 0
        self.error_counts[process_type] += 1

    def record_success(self, process_type: str):
        """记录成功"""
        if process_type not in self.success_counts:
            self.success_counts[process_type] = 0
        self.success_counts[process_type] += 1

    def record_command(self, process_type: str, command: str):
        """记录命令"""
        if process_type not in self.command_history:
            self.command_history[process_type] = deque(maxlen=100)
        self.command_history[process_type].append({
            "command": command,
            "timestamp": time.time()
        })

    def record_output(self, process_type: str, output: str):
        """记录输出"""
        if process_type not in self.output_history:
            self.output_history[process_type] = deque(maxlen=200)
        self.output_history[process_type].append({
            "output": output,
            "timestamp": time.time()
        })

    async def get_anomalies(
        self,
        anomaly_type: Optional[AnomalyType] = None,
        resolved: Optional[bool] = None,
        limit: int = 50
    ) -> List[Anomaly]:
        """获取异常记录"""
        anomalies = list(self.anomalies.values())

        # 过滤
        if anomaly_type:
            anomalies = [a for a in anomalies if a.anomaly_type == anomaly_type]

        if resolved is not None:
            anomalies = [a for a in anomalies if a.resolved == resolved]

        # 排序（最新的在前）
        anomalies.sort(key=lambda a: a.detected_at, reverse=True)

        # 限制数量
        return anomalies[:limit]

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_anomalies = len(self.anomalies)
        unresolved = sum(1 for a in self.anomalies.values() if not a.resolved)

        # 按类型统计
        by_type = {}
        for anomaly in self.anomalies.values():
            atype = anomaly.anomaly_type.value
            if atype not in by_type:
                by_type[atype] = 0
            by_type[atype] += 1

        # 按严重程度统计
        by_severity = {}
        for anomaly in self.anomalies.values():
            severity = anomaly.severity.value
            if severity not in by_severity:
                by_severity[severity] = 0
            by_severity[severity] += 1

        return {
            "total": total_anomalies,
            "unresolved": unresolved,
            "resolved": total_anomalies - unresolved,
            "by_type": by_type,
            "by_severity": by_severity,
            "is_running": self.is_running
        }

    async def resolve_anomaly(self, anomaly_id: str):
        """解决异常"""
        if anomaly_id in self.anomalies:
            self.anomalies[anomaly_id].resolved = True
            self.anomalies[anomaly_id].resolved_at = time.time()

            await self.output_router.emit_guardian(
                LogLevel.SUCCESS,
                f"异常已解决: {anomaly_id}"
            )

    async def clear_resolved(self):
        """清理已解决的异常"""
        to_remove = [
            anomaly_id for anomaly_id, anomaly in self.anomalies.items()
            if anomaly.resolved
        ]

        for anomaly_id in to_remove:
            del self.anomalies[anomaly_id]

        await self.output_router.emit_guardian(
            LogLevel.INFO,
            f"已清理 {len(to_remove)} 条已解决的异常"
        )


# 全局异常检测器实例
_global_anomaly_detector = None


def get_anomaly_detector(project_root: Path) -> AnomalyDetector:
    """获取全局异常检测器实例"""
    global _global_anomaly_detector

    if _global_anomaly_detector is None:
        _global_anomaly_detector = AnomalyDetector(project_root)

    return _global_anomaly_detector


def reset_anomaly_detector():
    """重置全局异常检测器"""
    global _global_anomaly_detector
    _global_anomaly_detector = None