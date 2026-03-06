#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 循环控制接口

提供对 AI 循环进程的控制功能：
- 启动/停止 AI 循环
- 暂停/恢复 AI 循环
- 获取 AI 循环状态
- 发送指令到 AI 循环
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.ipc import IPCManager


class AILoopState(Enum):
    """AI 循环状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class AILoopCommand(Enum):
    """AI 循环控制指令"""
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    RESTART = "restart"
    GET_STATUS = "get_status"
    SEND_MESSAGE = "send_message"
    GET_LOGS = "get_logs"


class AILoopController:
    """AI 循环控制器
    
    管理和控制 AI 循环进程的生命周期
    """
    
    def __init__(self, project_root: Path, config_file: str = "config.json"):
        self.project_root = project_root
        self.config_file = config_file
        self.ipc = IPCManager(project_root)
        
        self.process = None
        self.pid = None
        self.state = AILoopState.STOPPED
        
        # 启动命令
        self.startup_command = [
            sys.executable,
            str(project_root / "dev_bot" / "ai_loop_process.py"),
            str(project_root),
            config_file
        ]
        
        # 控制命令文件
        self.command_file = project_root / ".ipc" / "ai_loop_command.json"
        self.response_file = project_root / ".ipc" / "ai_loop_response.json"
        
        print(f"[AI循环控制器] 初始化完成，项目根目录: {project_root}")
    
    async def start(self) -> bool:
        """启动 AI 循环"""
        if self.state == AILoopState.RUNNING:
            print(f"[AI循环控制器] AI 循环已在运行")
            return True
        
        if self.state == AILoopState.STARTING:
            print(f"[AI循环控制器] AI 循环正在启动中...")
            return False
        
        try:
            print(f"[AI循环控制器] 启动 AI 循环...")
            self.state = AILoopState.STARTING
            
            # 启动进程
            self.process = await asyncio.create_subprocess_exec(
                *self.startup_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            self.pid = self.process.pid
            self.state = AILoopState.RUNNING
            
            # 保存状态到 IPC
            self.ipc.write_status("ai_loop", {
                "pid": self.pid,
                "state": self.state.value,
                "status": "running",
                "startup_command": self.startup_command
            })
            
            print(f"[AI循环控制器] AI 循环已启动（PID: {self.pid}）")
            return True
            
        except Exception as e:
            print(f"[AI循环控制器] 启动失败: {e}")
            self.state = AILoopState.ERROR
            return False
    
    async def stop(self) -> bool:
        """停止 AI 循环"""
        if self.state == AILoopState.STOPPED:
            print(f"[AI循环控制器] AI 循环已停止")
            return True
        
        if self.state == AILoopState.STOPPING:
            print(f"[AI循环控制器] AI 循环正在停止中...")
            return False
        
        try:
            print(f"[AI循环控制器] 停止 AI 循环...")
            self.state = AILoopState.STOPPING
            
            if self.process and self.pid:
                # 发送 SIGTERM
                os.kill(self.pid, signal.SIGTERM)
                
                # 等待进程退出
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    # 强制杀死
                    os.kill(self.pid, signal.SIGKILL)
                    await self.process.wait()
            
            self.process = None
            self.pid = None
            self.state = AILoopState.STOPPED
            
            # 更新 IPC 状态
            self.ipc.write_status("ai_loop", {
                "state": self.state.value,
                "status": "stopped"
            })
            
            print(f"[AI循环控制器] AI 循环已停止")
            return True
            
        except Exception as e:
            print(f"[AI循环控制器] 停止失败: {e}")
            self.state = AILoopState.ERROR
            return False
    
    async def pause(self) -> bool:
        """暂停 AI 循环"""
        if self.state != AILoopState.RUNNING:
            print(f"[AI循环控制器] AI 循环未运行，无法暂停")
            return False
        
        try:
            print(f"[AI循环控制器] 暂停 AI 循环...")
            
            # 发送暂停指令
            await self._send_command(AILoopCommand.PAUSE)
            
            # 等待响应
            response = await self._wait_for_response(timeout=5)
            
            if response and response.get("success"):
                self.state = AILoopState.PAUSED
                print(f"[AI循环控制器] AI 循环已暂停")
                return True
            else:
                print(f"[AI循环控制器] 暂停失败: {response.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"[AI循环控制器] 暂停失败: {e}")
            return False
    
    async def resume(self) -> bool:
        """恢复 AI 循环"""
        if self.state != AILoopState.PAUSED:
            print(f"[AI循环控制器] AI 循环未暂停，无法恢复")
            return False
        
        try:
            print(f"[AI循环控制器] 恢复 AI 循环...")
            
            # 发送恢复指令
            await self._send_command(AILoopCommand.RESUME)
            
            # 等待响应
            response = await self._wait_for_response(timeout=5)
            
            if response and response.get("success"):
                self.state = AILoopState.RUNNING
                print(f"[AI循环控制器] AI 循环已恢复")
                return True
            else:
                print(f"[AI循环控制器] 恢复失败: {response.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"[AI循环控制器] 恢复失败: {e}")
            return False
    
    async def restart(self) -> bool:
        """重启 AI 循环"""
        print(f"[AI循环控制器] 重启 AI 循环...")
        
        # 先停止
        if not await self.stop():
            return False
        
        # 等待一下
        await asyncio.sleep(1)
        
        # 再启动
        return await self.start()
    
    async def get_status(self) -> Dict[str, Any]:
        """获取 AI 循环状态"""
        # 检查进程是否还在运行
        if self.pid:
            try:
                os.kill(self.pid, 0)
            except OSError:
                # 进程不存在
                self.state = AILoopState.STOPPED
                self.pid = None
                self.process = None
        
        # 从 IPC 读取状态
        ipc_status = self.ipc.read_status("ai_loop")
        
        return {
            "state": self.state.value,
            "pid": self.pid,
            "ipc_status": ipc_status
        }
    
    async def send_message(self, message: str) -> bool:
        """发送消息到 AI 循环"""
        if self.state != AILoopState.RUNNING:
            print(f"[AI循环控制器] AI 循环未运行，无法发送消息")
            return False
        
        try:
            print(f"[AI循环控制器] 发送消息到 AI 循环: {message[:50]}...")
            
            # 发送消息指令
            await self._send_command(AILoopCommand.SEND_MESSAGE, {"message": message})
            
            # 等待响应
            response = await self._wait_for_response(timeout=10)
            
            if response and response.get("success"):
                print(f"[AI循环控制器] 消息已发送")
                return True
            else:
                print(f"[AI循环控制器] 消息发送失败: {response.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"[AI循环控制器] 发送消息失败: {e}")
            return False
    
    async def get_logs(self, lines: int = 100) -> list:
        """获取 AI 循环日志"""
        return self.ipc.read_logs("ai_loop", lines)
    
    async def _send_command(self, command: AILoopCommand, params: Dict = None):
        """发送命令到 AI 循环"""
        command_data = {
            "command": command.value,
            "params": params or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # 写入命令文件
        try:
            with open(self.command_file, 'w', encoding='utf-8') as f:
                json.dump(command_data, f)
        except Exception as e:
            print(f"[AI循环控制器] 写入命令失败: {e}")
    
    async def _wait_for_response(self, timeout: float = 5) -> Optional[Dict]:
        """等待 AI 循环响应"""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                if self.response_file.exists():
                    with open(self.response_file, 'r', encoding='utf-8') as f:
                        response = json.load(f)
                    
                    # 删除响应文件
                    self.response_file.unlink()
                    
                    return response
            except Exception:
                pass
            
            await asyncio.sleep(0.1)
        
        return None