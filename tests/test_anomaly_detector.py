"""测试异常检测系统

测试 AI 循环异常识别功能
"""
import pytest
import asyncio
import time
from pathlib import Path

from dev_bot.anomaly_detector import (
    AnomalyDetector,
    AnomalyType,
    AnomalySeverity,
    Anomaly,
    get_anomaly_detector,
    reset_anomaly_detector
)
from dev_bot.ipc import IPCManager


@pytest.mark.asyncio
async def test_anomaly_detector_init():
    """测试异常检测器初始化"""
    project_root = Path.cwd()
    detector = AnomalyDetector(project_root)

    assert detector.project_root == project_root
    assert detector.is_running is False
    assert len(detector.anomalies) == 0


@pytest.mark.asyncio
async def test_anomaly_detector_start_stop():
    """测试启动和停止"""
    project_root = Path.cwd()
    detector = AnomalyDetector(project_root)

    # 启动
    await detector.start()
    assert detector.is_running is True

    # 等待
    await asyncio.sleep(0.5)

    # 停止
    await detector.stop()
    assert detector.is_running is False


@pytest.mark.asyncio
async def test_record_heartbeat():
    """测试记录心跳"""
    project_root = Path.cwd()
    detector = AnomalyDetector(project_root)

    # 记录心跳
    detector.record_heartbeat("ai_loop")

    assert "ai_loop" in detector.heartbeats
    assert detector.heartbeats["ai_loop"] > 0


@pytest.mark.asyncio
async def test_record_error_success():
    """测试记录错误和成功"""
    project_root = Path.cwd()
    detector = AnomalyDetector(project_root)

    # 记录错误
    detector.record_error("ai_loop", "测试错误")
    assert detector.error_counts["ai_loop"] == 1

    # 记录成功
    detector.record_success("ai_loop")
    assert detector.success_counts["ai_loop"] == 1


@pytest.mark.asyncio
async def test_record_command():
    """测试记录命令"""
    project_root = Path.cwd()
    detector = AnomalyDetector(project_root)

    # 记录命令
    detector.record_command("ai_loop", "test command")

    assert "ai_loop" in detector.command_history
    assert len(detector.command_history["ai_loop"]) == 1
    assert detector.command_history["ai_loop"][0]["command"] == "test command"


@pytest.mark.asyncio
async def test_record_output():
    """测试记录输出"""
    project_root = Path.cwd()
    detector = AnomalyDetector(project_root)

    # 记录输出
    detector.record_output("ai_loop", "test output")

    assert "ai_loop" in detector.output_history
    assert len(detector.output_history["ai_loop"]) == 1
    assert detector.output_history["ai_loop"][0]["output"] == "test output"


@pytest.mark.asyncio
async def test_report_anomaly():
    """测试报告异常"""
    reset_anomaly_detector()
    project_root = Path.cwd()
    detector = get_anomaly_detector(project_root)

    # 报告异常
    await detector._report_anomaly(
        "test_anomaly",
        AnomalyType.NO_RESPONSE,
        AnomalySeverity.HIGH,
        "测试异常"
    )

    assert len(detector.anomalies) == 1
    assert "test_anomaly" in detector.anomalies

    anomaly = detector.anomalies["test_anomaly"]
    assert anomaly.anomaly_type == AnomalyType.NO_RESPONSE
    assert anomaly.severity == AnomalySeverity.HIGH
    assert anomaly.description == "测试异常"

    reset_anomaly_detector()


@pytest.mark.asyncio
async def test_get_anomalies():
    """测试获取异常"""
    reset_anomaly_detector()
    project_root = Path.cwd()
    detector = get_anomaly_detector(project_root)

    # 报告多个异常
    await detector._report_anomaly(
        "anomaly_1",
        AnomalyType.NO_RESPONSE,
        AnomalySeverity.HIGH,
        "异常1"
    )

    await asyncio.sleep(0.1)

    await detector._report_anomaly(
        "anomaly_2",
        AnomalyType.RATE_LIMIT,
        AnomalySeverity.MEDIUM,
        "异常2"
    )

    # 获取所有异常
    all_anomalies = await detector.get_anomalies()
    assert len(all_anomalies) == 2

    # 按类型过滤
    no_response = await detector.get_anomalies(
        anomaly_type=AnomalyType.NO_RESPONSE
    )
    assert len(no_response) == 1
    assert no_response[0].anomaly_type == AnomalyType.NO_RESPONSE

    reset_anomaly_detector()


@pytest.mark.asyncio
async def test_resolve_anomaly():
    """测试解决异常"""
    reset_anomaly_detector()
    project_root = Path.cwd()
    detector = get_anomaly_detector(project_root)

    # 报告异常
    await detector._report_anomaly(
        "test_anomaly",
        AnomalyType.NO_RESPONSE,
        AnomalySeverity.HIGH,
        "测试异常"
    )

    # 解决异常
    await detector.resolve_anomaly("test_anomaly")

    anomaly = detector.anomalies["test_anomaly"]
    assert anomaly.resolved is True
    assert anomaly.resolved_at is not None

    reset_anomaly_detector()


@pytest.mark.asyncio
async def test_clear_resolved():
    """测试清理已解决的异常"""
    reset_anomaly_detector()
    project_root = Path.cwd()
    detector = get_anomaly_detector(project_root)

    # 报告异常
    await detector._report_anomaly(
        "anomaly_1",
        AnomalyType.NO_RESPONSE,
        AnomalySeverity.HIGH,
        "异常1"
    )

    await detector._report_anomaly(
        "anomaly_2",
        AnomalyType.RATE_LIMIT,
        AnomalySeverity.MEDIUM,
        "异常2"
    )

    # 解决一个异常
    await detector.resolve_anomaly("anomaly_1")

    # 清理已解决的异常
    await detector.clear_resolved()

    assert len(detector.anomalies) == 1
    assert "anomaly_2" in detector.anomalies
    assert "anomaly_1" not in detector.anomalies

    reset_anomaly_detector()


@pytest.mark.asyncio
async def test_get_stats():
    """测试获取统计"""
    reset_anomaly_detector()
    project_root = Path.cwd()
    detector = get_anomaly_detector(project_root)

    # 报告异常
    await detector._report_anomaly(
        "anomaly_1",
        AnomalyType.NO_RESPONSE,
        AnomalySeverity.HIGH,
        "异常1"
    )

    await detector._report_anomaly(
        "anomaly_2",
        AnomalyType.RATE_LIMIT,
        AnomalySeverity.MEDIUM,
        "异常2"
    )

    # 获取统计
    stats = await detector.get_stats()

    assert stats["total"] == 2
    assert stats["unresolved"] == 2
    assert stats["resolved"] == 0
    assert "by_type" in stats
    assert "by_severity" in stats

    reset_anomaly_detector()


@pytest.mark.asyncio
async def test_detect_no_response():
    """测试检测无响应"""
    reset_anomaly_detector()
    project_root = Path.cwd()
    detector = get_anomaly_detector(project_root)
    ipc = IPCManager(project_root)

    # 创建过期的状态文件
    old_time = time.time() - 100  # 100秒前
    ipc.write_status("ai_loop", {
        "status": "running",
        "pid": 12345,
        "last_seen": old_time
    })

    # 检测无响应
    await detector._detect_no_response()

    # 应该检测到异常
    anomalies = await detector.get_anomalies(
        anomaly_type=AnomalyType.NO_RESPONSE
    )
    assert len(anomalies) > 0

    reset_anomaly_detector()


def test_anomaly_type_enum():
    """测试异常类型枚举"""
    assert AnomalyType.NO_RESPONSE.value == "no_response"
    assert AnomalyType.RATE_LIMIT.value == "rate_limit"
    assert AnomalyType.INVALID_COMMAND.value == "invalid_command"
    assert AnomalyType.INFINITE_LOOP.value == "infinite_loop"
    assert AnomalyType.MEMORY_LEAK.value == "memory_leak"
    assert AnomalyType.HIGH_ERROR_RATE.value == "high_error_rate"


def test_anomaly_severity_enum():
    """测试异常严重程度枚举"""
    assert AnomalySeverity.LOW.value == "low"
    assert AnomalySeverity.MEDIUM.value == "medium"
    assert AnomalySeverity.HIGH.value == "high"
    assert AnomalySeverity.CRITICAL.value == "critical"


def test_anomaly_to_dict():
    """测试异常转换为字典"""
    anomaly = Anomaly(
        anomaly_id="test_id",
        anomaly_type=AnomalyType.NO_RESPONSE,
        severity=AnomalySeverity.HIGH,
        description="测试异常"
    )

    data = anomaly.to_dict()

    assert data["anomaly_id"] == "test_id"
    assert data["anomaly_type"] == "no_response"
    assert data["severity"] == "high"
    assert data["description"] == "测试异常"


def test_global_anomaly_detector():
    """测试全局异常检测器"""
    reset_anomaly_detector()

    project_root = Path.cwd()
    detector1 = get_anomaly_detector(project_root)
    detector2 = get_anomaly_detector(project_root)

    # 应该是同一个实例
    assert detector1 is detector2

    # 重置
    reset_anomaly_detector()

    # 获取新实例
    detector3 = get_anomaly_detector(project_root)
    assert detector3 is not detector1

    reset_anomaly_detector()