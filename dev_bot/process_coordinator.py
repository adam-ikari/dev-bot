#!/usr/bin/env python3
"""
进程协调器

管理 TUI、AI 循环和守护进程三个独立进程
"""

import asyncio
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.ipc import IPCManager
from dev_bot.guardian_process import GuardianProcess


class ProcessCoordinator:
    """进程协调器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ipc = IPCManager(project_root)
        
        self.tui_process = None
        self.ai_loop_process = None
        self.guardian_process = None
        
        self.is_running = False
        self.pids = {
            "tui": None,
            "ai_loop": None,
            "guardian": None
        }
        
        # 注册信号处理
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)
    
    async def start_all(self):
        """启动所有进程"""
        self.is_running = True
        
        print("[协调器] 启动所有进程...")
        
        # 清理旧文件
        self.ipc.cleanup()
        
        # 启动守护进程（独立模式）
        await self._start_guardian()
        
        # 启动 AI 循环进程
        await self._start_ai_loop()
        
        # 启动 TUI 进程（阻塞）
        await self._start_tui()
    
    async def _start_guardian(self):
        """启动守护进程（分层架构版本）"""
        try:
            script = self.project_root / "dev_bot" / "guardian_process.py"
            cmd = [
                sys.executable,
                str(script),
                "standalone",  # 独立模式
                "30",  # 检查间隔
                # 可以添加配置文件路径
                # str(self.project_root / "guardian_config.json")
            ]
            
            self.guardian_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            self.pids["guardian"] = self.guardian_process.pid
            print(f"[协调器] 守护进程已启动（PID: {self.guardian_process.pid}，分层架构）")
            
            # 保存守护进程状态
            self.ipc.write_status("guardian", {
                "pid": self.guardian_process.pid,
                "status": "running",
                "architecture": "layered",  # 标记为分层架构
                "version": "2.0"
            })
            
        except Exception as e:
            print(f"[协调器] 启动守护进程失败: {e}")
    
    async def _start_ai_loop(self):
        """启动 AI 循环进程"""
        try:
            script = self.project_root / "dev_bot" / "ai_loop_process.py"
            cmd = [
                sys.executable,
                str(script),
                str(self.project_root),
                "config.json"
            ]
            
            self.ai_loop_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            self.pids["ai_loop"] = self.ai_loop_process.pid
            print(f"[协调器] AI 循环进程已启动（PID: {self.ai_loop_process.pid}）")
            
            # 保存 AI 循环状态和启动命令
            self.ipc.write_status("ai_loop", {
                "pid": self.ai_loop_process.pid,
                "status": "running",
                "startup_command": cmd
            })
            
        except Exception as e:
            print(f"[协调器] 启动 AI 循环进程失败: {e}")
    
    async def _start_tui(self):
        """启动 TUI 进程"""
        try:
            # TUI 进程就是当前进程
            self.pids["tui"] = os.getpid()
            print(f"[协调器] TUI 进程（当前进程，PID: {os.getpid()}）")
            
            # 保存 TUI 状态和启动命令
            self.ipc.write_status("tui", {
                "pid": self.pids["tui"],
                "status": "running",
                "startup_command": [sys.executable, str(self.project_root / "dev_bot" / "process_coordinator.py")]
            })
            
            # 运行 TUI
            from dev_bot.tui import DevBotTUI
            
            app = DevBotTUI()
            await app.run_async()
            
        except Exception as e:
            print(f"[协调器] TUI 进程出错: {e}")
    
    async def stop_all(self):
        """停止所有进程"""
        self.is_running = False
        
        print("[协调器] 停止所有进程...")
        
        # 停止守护进程
        if self.pids["guardian"]:
            await self._stop_process("guardian", self.pids["guardian"])
        
        # 停止 AI 循环进程
        if self.pids["ai_loop"]:
            await self._stop_process("ai_loop", self.pids["ai_loop"])
        
        # 清理 IPC 文件
        self.ipc.cleanup()
        
        print("[协调器] 所有进程已停止")
    
    async def _stop_process(self, name: str, pid: int):
        """停止进程"""
        try:
            print(f"[协调器] 停止 {name} 进程（PID: {pid}）...")
            
            # 发送 SIGTERM
            os.kill(pid, signal.SIGTERM)
            
            # 等待进程退出
            for _ in range(10):
                try:
                    os.kill(pid, 0)
                    await asyncio.sleep(0.5)
                except OSError:
                    print(f"[协调器] {name} 进程已停止")
                    return
            
            # 强制杀死
            os.kill(pid, signal.SIGKILL)
            print(f"[协调器] {name} 进程已被强制停止")
            
        except Exception as e:
            print(f"[协调器] 停止 {name} 进程失败: {e}")
    
    def _handle_sigterm(self, signum, frame):
        """处理 SIGTERM 信号"""
        print(f"[协调器] 收到 SIGTERM 信号，准备停止所有进程...")
        self.is_running = False
    
    def _handle_sigint(self, signum, frame):
        """处理 SIGINT 信号"""
        print(f"[协调器] 收到 SIGINT 信号，准备停止所有进程...")
        self.is_running = False
    
    def get_status(self) -> Dict:
        """获取所有进程状态"""
        return {
            "tui": self.ipc.read_status("tui"),
            "ai_loop": self.ipc.read_status("ai_loop"),
            "guardian": self.ipc.read_status("guardian"),
            "pids": self.pids
        }
    
    def get_logs(self, process_type: str, lines: int = 100) -> List[str]:
        """获取日志"""
        return self.ipc.read_logs(process_type, lines)


async def main():
    """主函数"""
    project_root = Path.cwd()
    
    coordinator = ProcessCoordinator(project_root)
    
    try:
        await coordinator.start_all()
    except Exception as e:
        print(f"[协调器] 协调器出错: {e}")
    finally:
        await coordinator.stop_all()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[协调器] 协调器已停止")
