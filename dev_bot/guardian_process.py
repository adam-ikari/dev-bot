#!/usr/bin/env python3
"""
AI 守护进程 - 独立进程运行（分层架构版本）

使用分层架构实现 AI 守护进程：
- 底层守护层（不可变）：核心监控和恢复功能
- 上层业务逻辑层（可变）：业务规则和策略
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.ipc import IPCManager
from dev_bot.guardian import AIGuardian
from dev_bot.guardian.core import DefaultHealthChecker, DefaultRecoveryStrategy


class GuardianProcess:
    """AI 守护进程（使用分层架构）"""
    
    def __init__(self, check_interval: int = 30, config_file: Optional[Path] = None):
        self.check_interval = check_interval
        self.status_file = Path(".guardian-status.json")
        self.ipc = IPCManager(Path.cwd())
        self.config_file = config_file
        
        # 创建分层守护实例
        self.ai_guardian = AIGuardian(
            check_interval=check_interval,
            config_file=config_file
        )
        
        # 注册信号处理
        import signal
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)
    
    async def run(self):
        """运行守护进程"""
        print(f"[守护进程] 启动守护进程（PID: {os.getpid()}）")
        print(f"[守护进程] 检查间隔: {self.check_interval}秒")
        print(f"[守护进程] 架构: 分层架构（核心层 + 业务层）")
        
        # 初始化要监控的进程
        await self._init_monitored_processes()
        
        # 启动守护
        await self.ai_guardian.start()
        
        # 主循环（保持进程运行）
        try:
            while True:
                await asyncio.sleep(1)
                # 定期保存状态
                self._save_status()
        except asyncio.CancelledError:
            pass
        finally:
            await self.ai_guardian.stop()
            self._save_status({"status": "stopped"})
    
    async def _init_monitored_processes(self):
        """初始化要监控的进程"""
        project_root = Path.cwd()
        
        # 注册 AI 循环进程
        ai_loop_cmd = [
            sys.executable,
            str(project_root / "dev_bot" / "ai_loop_process.py"),
            str(project_root),
            "config.json"
        ]
        self.ai_guardian.register_process(
            "ai_loop",
            None,  # 初始没有 PID
            ai_loop_cmd,
            max_restarts=10
        )
        
        # 注册 TUI 进程
        tui_cmd = [
            sys.executable,
            str(project_root / "dev_bot" / "process_coordinator.py")
        ]
        self.ai_guardian.register_process(
            "tui",
            None,  # 初始没有 PID
            tui_cmd,
            max_restarts=10
        )
        
        print(f"[守护进程] 已初始化监控进程：ai_loop, tui")
    
    def register_process(self, process_type: str, pid: int, startup_command: List[str]):
        """注册进程（由进程启动后调用）"""
        self.ai_guardian.register_process(process_type, pid, startup_command)
        self.ai_guardian.update_process_status(process_type, pid)
        print(f"[守护进程] 已注册 {process_type} 进程（PID: {pid}）")
    
    def update_process_status(self, process_type: str, pid: int):
        """更新进程状态"""
        self.ai_guardian.update_process_status(process_type, pid)
    
    def _save_status(self, custom_status: Dict = None):
        """保存守护进程状态"""
        status = custom_status or self.ai_guardian.get_status()
        status["pid"] = os.getpid()
        
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2, default=str)
        except Exception as e:
            print(f"[守护进程] 保存状态失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return self.ai_guardian.get_status()
    
    def _handle_sigterm(self, signum, frame):
        """处理 SIGTERM 信号"""
        print(f"[守护进程] 收到 SIGTERM 信号，准备退出...")
        # 创建异步任务来停止守护
        asyncio.create_task(self.ai_guardian.stop())
    
    def _handle_sigint(self, signum, frame):
        """处理 SIGINT 信号"""
        print(f"[守护进程] 收到 SIGINT 信号，准备退出...")
        # 创建异步任务来停止守护
        asyncio.create_task(self.ai_guardian.stop())


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python guardian_process.py standalone [检查间隔] [配置文件]")
        sys.exit(1)
    
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    config_file = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    
    guardian = GuardianProcess(
        check_interval=check_interval,
        config_file=config_file
    )
    
    if sys.argv[1] != "standalone":
        print("警告: 当前版本仅支持 standalone 模式")
        print("用法: python guardian_process.py standalone [检查间隔] [配置文件]")
        sys.exit(1)
    
    print(f"[守护进程] 独立模式：自动管理所有进程")
    await guardian.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[守护进程] 守护进程已停止")
