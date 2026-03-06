#!/usr/bin/env python3
"""
进程间通信（IPC）模块

提供进程间通信的工具函数
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class IPCManager:
    """进程间通信管理器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ipc_dir = project_root / ".ipc"
        self.ipc_dir.mkdir(exist_ok=True)
        
        # 状态文件
        self.tui_status_file = self.ipc_dir / "tui-status.json"
        self.ai_loop_status_file = self.ipc_dir / "ai-loop-status.json"
        self.guardian_status_file = self.ipc_dir / "guardian-status.json"
        
        # 日志管道
        self.tui_log_pipe = self.ipc_dir / "tui-log.pipe"
        self.ai_loop_log_pipe = self.ipc_dir / "ai-loop-log.pipe"
        
    def write_status(self, process_type: str, status: Dict[str, Any]):
        """写入进程状态"""
        if process_type == "tui":
            status_file = self.tui_status_file
        elif process_type == "ai_loop":
            status_file = self.ai_loop_status_file
        elif process_type == "guardian":
            status_file = self.guardian_status_file
        else:
            raise ValueError(f"未知的进程类型: {process_type}")
        
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            print(f"[IPC] 写入状态失败: {e}")
    
    def read_status(self, process_type: str) -> Optional[Dict[str, Any]]:
        """读取进程状态"""
        if process_type == "tui":
            status_file = self.tui_status_file
        elif process_type == "ai_loop":
            status_file = self.ai_loop_status_file
        elif process_type == "guardian":
            status_file = self.guardian_status_file
        else:
            raise ValueError(f"未知的进程类型: {process_type}")
        
        if not status_file.exists():
            return None
        
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[IPC] 读取状态失败: {e}")
            return None
    
    def write_log(self, process_type: str, level: str, message: str):
        """写入日志"""
        log_file = self.ipc_dir / f"{process_type}.log"
        
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"[IPC] 写入日志失败: {e}")
    
    def read_logs(self, process_type: str, lines: int = 100) -> list:
        """读取日志"""
        log_file = self.ipc_dir / f"{process_type}.log"
        
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            return all_lines[-lines:]
        except Exception as e:
            print(f"[IPC] 读取日志失败: {e}")
            return []
    
    def cleanup(self):
        """清理 IPC 文件"""
        try:
            for file in self.ipc_dir.glob("*"):
                file.unlink()
            print(f"[IPC] IPC 文件已清理")
        except Exception as e:
            print(f"[IPC] 清理失败: {e}")
