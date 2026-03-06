#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后台系统管理器

管理 AI 守护和多 AI 实例作为后台进程运行
TUI 作为前台程序，通过 IPC 与后台进程通信
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from dev_bot.process_manager import ProcessManager
from dev_bot.ipc import IPCManager


class BackgroundSystem:
    """后台系统管理器
    
    管理所有后台进程：
    - AI 守护进程
    - 多 AI 实例进程
    
    TUI 作为前台进程，通过 IPC 与这些后台进程通信
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.process_manager = ProcessManager()
        self.ipc_manager = IPCManager(project_root)
        
        # 后台进程配置
        self.background_processes = {
            "guardian": {
                "script": "dev_bot/guardian_process.py",
                "args": [],
                "description": "AI 守护进程"
            },
            "ai_loop_analyzer": {
                "script": "dev_bot/ai_loop_process.py",
                "args": ["--role", "analyzer"],
                "description": "AI 分析实例"
            },
            "ai_loop_developer": {
                "script": "dev_bot/ai_loop_process.py",
                "args": ["--role", "developer"],
                "description": "AI 开发实例"
            },
            "ai_loop_tester": {
                "script": "dev_bot/ai_loop_process.py",
                "args": ["--role", "tester"],
                "description": "AI 测试实例"
            },
            "ai_loop_reviewer": {
                "script": "dev_bot/ai_loop_process.py",
                "args": ["--role", "reviewer"],
                "description": "AI 评审实例"
            }
        }
        
        # 进程状态
        self.process_status: Dict[str, Dict[str, Any]] = {}
        
        # 运行标志
        self.is_running = False
    
    async def start(self):
        """启动所有后台进程"""
        self.is_running = True
        
        print(f"[后台系统] 启动后台进程...")
        
        for process_id, config in self.background_processes.items():
            try:
                script_path = self.project_root / config["script"]
                
                if not script_path.exists():
                    print(f"[后台系统] 警告: 脚本不存在: {script_path}")
                    continue
                
                process = await self.process_manager.create_process(
                    process_id=process_id,
                    script_path=script_path,
                    args=config["args"],
                    cwd=self.project_root
                )
                
                if process:
                    self.process_status[process_id] = {
                        "pid": process.pid,
                        "status": "running",
                        "description": config["description"],
                        "started_at": asyncio.get_event_loop().time()
                    }
                    
                    print(f"[后台系统] ✓ {config['description']} (PID: {process.pid})")
                else:
                    print(f"[后台系统] ✗ {config['description']} 启动失败")
            
            except Exception as e:
                print(f"[后台系统] ✗ 启动 {process_id} 失败: {e}")
        
        # 更新 IPC 状态
        self._update_ipc_status()
        
        print(f"[后台系统] 后台进程启动完成")
    
    async def stop(self):
        """停止所有后台进程"""
        self.is_running = False
        
        print(f"[后台系统] 停止后台进程...")
        
        for process_id in list(self.process_status.keys()):
            await self._stop_process(process_id)
        
        print(f"[后台系统] 后台进程已停止")
    
    async def _stop_process(self, process_id: str):
        """停止单个进程"""
        if process_id in self.process_status:
            try:
                success = await self.process_manager.terminate_process(process_id)
                
                if success:
                    status = self.process_status[process_id]
                    print(f"[后台系统] ✓ 停止 {status['description']} (PID: {status['pid']})")
                    del self.process_status[process_id]
                else:
                    print(f"[后台系统] ✗ 停止 {process_id} 失败")
            
            except Exception as e:
                print(f"[后台系统] ✗ 停止 {process_id} 出错: {e}")
    
    def _update_ipc_status(self):
        """更新 IPC 状态"""
        status = {
            "is_running": self.is_running,
            "processes": self.process_status,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        self.ipc_manager.write_status("background_system", status)
    
    def get_status(self) -> Dict[str, Any]:
        """获取后台系统状态"""
        return {
            "is_running": self.is_running,
            "process_count": len(self.process_status),
            "processes": self.process_status
        }
    
    async def restart_process(self, process_id: str):
        """重启单个进程"""
        print(f"[后台系统] 重启进程: {process_id}")
        
        # 停止旧进程
        await self._stop_process(process_id)
        
        # 启动新进程
        if process_id in self.background_processes:
            config = self.background_processes[process_id]
            script_path = self.project_root / config["script"]
            
            process = await self.process_manager.create_process(
                process_id=process_id,
                script_path=script_path,
                args=config["args"],
                cwd=self.project_root
            )
            
            if process:
                self.process_status[process_id] = {
                    "pid": process.pid,
                    "status": "running",
                    "description": config["description"],
                    "started_at": asyncio.get_event_loop().time(),
                    "restarted_at": asyncio.get_event_loop().time()
                }
                
                print(f"[后台系统] ✓ {config['description']} 已重启 (PID: {process.pid})")
            
            self._update_ipc_status()
    
    async def monitor_processes(self):
        """监控后台进程状态"""
        while self.is_running:
            try:
                # 检查进程是否还在运行
                for process_id in list(self.process_status.keys()):
                    process = self.process_manager.processes.get(process_id)
                    
                    if process:
                        return_code = process.returncode
                        
                        if return_code is not None:
                            # 进程已退出
                            status = self.process_status[process_id]
                            print(f"[后台系统] 警告: {status['description']} 已退出 (返回码: {return_code})")
                            
                            # 尝试重启
                            await self.restart_process(process_id)
                
                # 更新 IPC 状态
                self._update_ipc_status()
                
                # 等待一段时间
                await asyncio.sleep(5)
            
            except Exception as e:
                print(f"[后台系统] 监控出错: {e}")
                await asyncio.sleep(5)


# 全局后台系统实例
_global_background_system: Optional[BackgroundSystem] = None


def get_background_system(project_root: Path) -> BackgroundSystem:
    """获取全局后台系统实例"""
    global _global_background_system
    
    if _global_background_system is None:
        _global_background_system = BackgroundSystem(project_root)
    
    return _global_background_system


def reset_background_system():
    """重置全局后台系统"""
    global _global_background_system
    _global_background_system = None