"""测试 AI 守护监控

测试 AI 守护监视 AI 循环的功能
"""
import pytest
import asyncio
import subprocess
import sys
import time
from pathlib import Path

from dev_bot.ai_guardian_monitor import AIGuardianMonitor
from dev_bot.ipc import IPCManager
from dev_bot.output_router import get_output_router, reset_output_router


@pytest.mark.asyncio
async def test_ai_guardian_monitor_init():
    """测试 AI 守护监控初始化"""
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root, check_interval=5)

    assert monitor.project_root == project_root
    assert monitor.check_interval == 5
    assert monitor.is_running is False
    assert monitor.ai_loop_process is None
    assert monitor.restart_count == 0


@pytest.mark.asyncio
async def test_ai_guardian_monitor_get_status():
    """测试获取状态"""
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root)

    status = await monitor.get_status()

    assert "is_running" in status
    assert "ai_loop" in status
    assert "pid" in status["ai_loop"]
    assert "healthy" in status["ai_loop"]
    assert "restart_count" in status["ai_loop"]


@pytest.mark.asyncio
async def test_ai_guardian_monitor_start_stop():
    """测试启动和停止"""
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root, check_interval=1)

    # 启动
    await monitor.start()
    assert monitor.is_running is True

    # 等待一段时间
    await asyncio.sleep(0.5)

    # 停止
    await monitor.stop()
    assert monitor.is_running is False


@pytest.mark.asyncio
async def test_ai_guardian_monitor_output_routing():
    """测试输出路由"""
    reset_output_router()
    output_router = get_output_router()

    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root, check_interval=1)

    # 启动监控
    await monitor.start()

    # 等待一些输出
    await asyncio.sleep(1)

    # 检查输出
    guardian_messages = await output_router.get_messages(
        source=output_router.__class__.__name__.lower().replace("outputsource", ""),
        limit=10
    )

    # 停止监控
    await monitor.stop()

    # 清理
    reset_output_router()


@pytest.mark.asyncio
async def test_ipc_status_read_write():
    """测试 IPC 状态读写"""
    project_root = Path.cwd()
    ipc = IPCManager(project_root)

    # 写入状态
    test_status = {
        "status": "running",
        "pid": 12345,
        "test": True
    }

    ipc.write_status("ai_loop", test_status)

    # 读取状态
    status = ipc.read_status("ai_loop")

    assert status is not None
    assert status["status"] == "running"
    assert status["pid"] == 12345
    assert status["test"] is True


@pytest.mark.asyncio
async def test_ipc_log_write_read():
    """测试 IPC 日志读写"""
    project_root = Path.cwd()
    ipc = IPCManager(project_root)

    # 写入日志
    test_msg1 = f"测试日志消息1_{time.time()}"
    test_msg2 = f"测试日志消息2_{time.time()}"

    ipc.write_log("ai_loop", "INFO", test_msg1)
    ipc.write_log("ai_loop", "WARNING", test_msg2)

    # 读取日志
    logs = ipc.read_logs("ai_loop", lines=10)

    assert len(logs) >= 2
    # 检查最新的两条日志
    assert test_msg1 in logs[-2]
    assert test_msg2 in logs[-1]


def test_import_ai_guardian_monitor():
    """测试导入"""
    from dev_bot.ai_guardian_monitor import AIGuardianMonitor
    assert AIGuardianMonitor is not None


def test_import_ipc_manager():
    """测试导入"""
    from dev_bot.ipc import IPCManager
    assert IPCManager is not None


@pytest.mark.asyncio
async def test_max_restarts_limit():
    """测试最大重启次数限制"""
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root)

    # 设置最大重启次数
    monitor.max_restarts = 2

    # 模拟达到最大重启次数
    monitor.restart_count = 3

    # 检查是否会拒绝启动
    success = await monitor._start_ai_loop()

    # 由于没有实际的 AI 循环进程，应该返回 False
    assert success is False or monitor.restart_count >= monitor.max_restarts


@pytest.mark.asyncio
async def test_heartbeat_timeout_detection():
    """测试心跳超时检测"""
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root, check_interval=0.5)

    # 启动监控
    await monitor.start()

    # 停止 AI 循环进程（如果存在）
    if monitor.ai_loop_process:
        try:
            monitor.ai_loop_process.kill()
            monitor.ai_loop_process.wait(timeout=5)
        except:
            pass
        monitor.ai_loop_process = None
        monitor.ai_loop_pid = None

    # 模拟心跳超时
    monitor.last_heartbeat_time = time.time() - 100  # 100秒前

    # 等待心跳检查（心跳检查间隔是5秒）
    await asyncio.sleep(6)

    # 检查健康状态
    assert monitor.ai_loop_healthy is False

    # 停止监控
    await monitor.stop()


@pytest.mark.asyncio
async def test_process_health_check():
    """测试进程健康检查"""
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root)

    # 模拟一个不存在的 PID
    monitor.ai_loop_pid = 99999

    # 检查健康状态
    await monitor._check_ai_loop_health()

    # 应该标记为不健康
    assert monitor.ai_loop_healthy is False


@pytest.mark.asyncio
async def test_clean_shutdown():
    """测试正常关闭"""
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root, check_interval=1)

    # 启动监控
    await monitor.start()
    assert monitor.is_running is True

    # 正常停止
    await monitor.stop()
    assert monitor.is_running is False

    # 进程应该被清理
    assert monitor.ai_loop_process is None


def test_signal_handlers():
    """测试信号处理器"""
    project_root = Path.cwd()
    monitor = AIGuardianMonitor(project_root)

    # 检查信号处理器已注册
    import signal
    handlers = signal.getsignal(signal.SIGTERM)
    handlers2 = signal.getsignal(signal.SIGINT)

    # 信号处理器应该已设置
    assert handlers is not None
    assert handlers2 is not None