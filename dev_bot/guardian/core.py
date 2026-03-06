#!/usr/bin/env python3
"""
AI 守护进程 - 核心守护层（不可变）

提供基础的进程监控、健康检查和自动恢复功能
这一层是稳定的、不可变的，确保系统可靠运行
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable


class HealthChecker(ABC):
    """健康检查器抽象基类"""
    
    @abstractmethod
    async def check(self, process_info: Dict[str, Any]) -> bool:
        """检查进程是否健康"""
        pass


class DefaultHealthChecker(HealthChecker):
    """默认健康检查器"""
    
    def __init__(self):
        self.max_last_seen_interval = 60  # 最大允许的未响应时间（秒）
    
    async def check(self, process_info: Dict[str, Any]) -> bool:
        """检查进程是否健康"""
        # 检查进程是否存在
        pid = process_info.get("pid")
        if not pid or not self._is_process_alive(pid):
            return False
        
        # 检查最后响应时间
        last_seen = process_info.get("last_seen")
        if last_seen:
            elapsed = time.time() - last_seen
            if elapsed > self.max_last_seen_interval:
                return False
        
        return True
    
    def _is_process_alive(self, pid: int) -> bool:
        """检查进程是否存在"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


class RecoveryStrategy(ABC):
    """恢复策略抽象基类"""
    
    @abstractmethod
    async def recover(self, process_type: str, process_info: Dict[str, Any]) -> bool:
        """执行恢复操作"""
        pass


class DefaultRecoveryStrategy(RecoveryStrategy):
    """默认恢复策略"""
    
    def __init__(self, ipc_manager):
        self.ipc_manager = ipc_manager
    
    async def recover(self, process_type: str, process_info: Dict[str, Any]) -> bool:
        """执行默认恢复操作：重启进程"""
        # 获取启动命令
        startup_command = process_info.get("startup_command")
        if not startup_command:
            return False
        
        # 检查重启次数
        restart_count = process_info.get("restart_count", 0)
        max_restarts = process_info.get("max_restarts", 10)
        
        if restart_count >= max_restarts:
            print(f"[守护层] {process_type} 重启次数已达上限（{max_restarts}），停止尝试")
            return False
        
        try:
            # 启动进程
            process = await asyncio.create_subprocess_exec(
                *startup_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # 更新进程信息
            process_info["pid"] = process.pid
            process_info["last_seen"] = time.time()
            process_info["restart_count"] = restart_count + 1
            
            print(f"[守护层] {process_type} 已重启（PID: {process.pid}，第 {process_info['restart_count']} 次）")
            
            return True
            
        except Exception as e:
            print(f"[守护层] 重启 {process_type} 失败: {e}")
            return False


class CoreGuardian:
    """核心守护层（不可变）
    
    提供基础的进程监控和自动恢复功能
    """
    
    def __init__(
        self,
        check_interval: int = 30,
        health_checker: Optional[HealthChecker] = None,
        recovery_strategy: Optional[RecoveryStrategy] = None,
        on_status_update: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.check_interval = check_interval
        self.health_checker = health_checker or DefaultHealthChecker()
        self.recovery_strategy = recovery_strategy
        self.on_status_update = on_status_update
        
        self.is_running = False
        self._task = None
        self.recovery_count = 0
        self.last_check_time = None
        
        # 监控的进程
        self.monitored_processes: Dict[str, Dict[str, Any]] = {}
        
        # 注册信号处理
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)
    
    def register_process(
        self,
        process_type: str,
        pid: Optional[int],
        startup_command: List[str],
        max_restarts: int = 10
    ):
        """注册要监控的进程"""
        self.monitored_processes[process_type] = {
            "pid": pid,
            "last_seen": time.time() if pid else None,
            "restart_count": 0,
            "max_restarts": max_restarts,
            "startup_command": startup_command,
            "process_type": process_type
        }
        print(f"[守护层] 已注册 {process_type} 进程监控")
    
    def update_process_status(self, process_type: str, pid: int):
        """更新进程状态（由进程本身调用）"""
        if process_type in self.monitored_processes:
            self.monitored_processes[process_type]["pid"] = pid
            self.monitored_processes[process_type]["last_seen"] = time.time()
            print(f"[守护层] 更新 {process_type} 进程状态（PID: {pid}）")
    
    async def start(self):
        """启动守护层"""
        if self.is_running:
            print("[守护层] 守护层已在运行")
            return
        
        self.is_running = True
        print(f"[守护层] 启动核心守护层（PID: {os.getpid()}，检查间隔: {self.check_interval}秒）")
        
        # 创建后台任务
        self._task = asyncio.create_task(self._guard_loop())
    
    async def stop(self):
        """停止守护层"""
        if not self.is_running:
            return
        
        self.is_running = False
        print("[守护层] 停止核心守护层")
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _guard_loop(self):
        """守护循环"""
        while self.is_running:
            try:
                await self._check_all_processes()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[守护层] 守护循环出错: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_all_processes(self):
        """检查所有监控的进程"""
        self.last_check_time = time.time()
        
        for process_type, process_info in self.monitored_processes.items():
            await self._check_process(process_type, process_info)
        
        # 通知状态更新
        if self.on_status_update:
            self.on_status_update(self.get_status())
    
    async def _check_process(self, process_type: str, process_info: Dict[str, Any]):
        """检查单个进程"""
        # 检查进程健康状态
        is_healthy = await self.health_checker.check(process_info)
        
        if is_healthy:
            print(f"[守护层] {process_type} 进程运行正常（PID: {process_info.get('pid')}）")
        else:
            print(f"[守护层] {process_type} 进程需要恢复...")
            
            # 执行恢复
            if self.recovery_strategy:
                success = await self.recovery_strategy.recover(process_type, process_info)
                if success:
                    self.recovery_count += 1
                    print(f"[守护层] {process_type} 恢复成功（总恢复次数: {self.recovery_count}）")
                else:
                    print(f"[守护层] {process_type} 恢复失败")
    
    def get_status(self) -> Dict[str, Any]:
        """获取守护层状态"""
        return {
            "is_running": self.is_running,
            "recovery_count": self.recovery_count,
            "last_check_time": self.last_check_time,
            "check_interval": self.check_interval,
            "monitored_processes": dict(self.monitored_processes),
            "pid": os.getpid()
        }
    
    def get_process_status(self, process_type: str) -> Optional[Dict[str, Any]]:
        """获取特定进程的状态"""
        return self.monitored_processes.get(process_type)
    
    def _handle_sigterm(self, signum, frame):
        """处理 SIGTERM 信号"""
        print(f"[守护层] 收到 SIGTERM 信号，准备退出...")
        self.is_running = False
    
    def _handle_sigint(self, signum, frame):
        """处理 SIGINT 信号"""
        print(f"[守护层] 收到 SIGINT 信号，准备退出...")
        self.is_running = False