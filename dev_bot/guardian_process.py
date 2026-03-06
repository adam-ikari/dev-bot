#!/usr/bin/env python3
"""
AI 守护进程 - 独立进程运行（分层架构版本）

使用分层架构实现 AI 守护进程：
- 底层守护层（不可变）：核心监控和恢复功能
- 上层业务逻辑层（可变）：业务规则和策略
- 集成 IPC Server 进行实时通讯
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
from dev_bot.ipc_realtime import IPCServer, IPCMessage, IPCMessageType
from dev_bot.guardian import AIGuardian
from dev_bot.guardian.core import DefaultHealthChecker, DefaultRecoveryStrategy


class GuardianProcess:
    """AI 守护进程（使用分层架构 + IPC）"""
    
    def __init__(self, check_interval: int = 30, config_file: Optional[Path] = None):
        self.check_interval = check_interval
        self.status_file = Path(".guardian-status.json")
        self.ipc = IPCManager(Path.cwd())
        self.config_file = config_file
        
        # IPC Server
        self.ipc_server = None
        self.ipc_socket_path = Path.cwd() / ".ipc" / "guardian.sock"
        
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
        print(f"[守护进程] IPC: Unix Socket 实时通讯")
        
        # 启动 IPC Server
        await self._start_ipc_server()
        
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
                # 定期广播心跳
                await self._broadcast_status()
        except asyncio.CancelledError:
            pass
        finally:
            await self.ai_guardian.stop()
            await self._stop_ipc_server()
            self._save_status({"status": "stopped"})
    
    async def _start_ipc_server(self):
        """启动 IPC Server"""
        try:
            self.ipc_server = IPCServer(self.ipc_socket_path)
            await self.ipc_server.start()
            
            # 注册消息处理器
            self.ipc_server.on(IPCMessageType.PROCESS_REGISTER, self._handle_process_register)
            self.ipc_server.on(IPCMessageType.PROCESS_STATUS, self._handle_process_status)
            self.ipc_server.on(IPCMessageType.PROCESS_EXIT, self._handle_process_exit)
            self.ipc_server.on(IPCMessageType.SYSTEM_COMMAND, self._handle_system_command)
            
            print(f"[守护进程] IPC Server 已启动")
        except Exception as e:
            print(f"[守护进程] 启动 IPC Server 失败: {e}")
    
    async def _stop_ipc_server(self):
        """停止 IPC Server"""
        if self.ipc_server:
            await self.ipc_server.stop()
    
    async def _broadcast_status(self):
        """广播状态给所有连接的客户端"""
        if not self.ipc_server:
            return
        
        # 获取守护进程状态
        status = self._get_status()
        
        # 创建状态消息
        message = IPCMessage(
            message_type=IPCMessageType.SYSTEM_STATUS,
            data=status,
            source="guardian"
        )
        
        # 广播给所有客户端
        await self.ipc_server.broadcast(message)
    
    async def _handle_process_register(self, client_id: str, message: IPCMessage):
        """处理进程注册消息"""
        process_id = message.data.get("process_id")
        process_type = message.data.get("type")
        
        print(f"[守护进程] 进程注册: {process_id} ({process_type})")
        
        # 可以在这里注册到守护进程管理
        # 目前暂时只记录
        self.ipc.write_log("guardian", "info", f"进程注册: {process_id} ({process_type}) from {client_id}")
    
    async def _handle_process_status(self, client_id: str, message: IPCMessage):
        """处理进程状态更新消息"""
        process_id = message.data.get("process_id")
        status = message.data.get("status")
        
        print(f"[守护进程] 进程状态更新: {process_id} -> {status}")
        
        # 可以在这里更新进程状态
        self.ipc.write_log("guardian", "info", f"进程状态: {process_id} -> {status}")
    
    async def _handle_process_exit(self, client_id: str, message: IPCMessage):
        """处理进程退出消息"""
        process_id = message.data.get("process_id")
        exit_code = message.data.get("exit_code")
        
        print(f"[守护进程] 进程退出: {process_id} (退出码: {exit_code})")
        
        # 可以在这里触发重启逻辑
        self.ipc.write_log("guardian", "warning", f"进程退出: {process_id} (退出码: {exit_code})")
    
    async def _handle_system_command(self, client_id: str, message: IPCMessage):
        """处理系统命令"""
        command = message.data.get("command")
        params = message.data.get("params", {})
        
        print(f"[守护进程] 收到系统命令: {command} from {client_id}")
        
        # 处理命令
        if command == "get_status":
            status = self._get_status()
            response = IPCMessage(
                message_type="system_response",
                data={"command": command, "result": status},
                source="guardian"
            )
            await self.ipc_server.send_to(client_id, response)
        
        elif command == "restart_process":
            process_id = params.get("process_id")
            # 实现重启逻辑
            await self._restart_process(process_id)
    
    async def _restart_process(self, process_id: str):
        """重启进程"""
        print(f"[守护进程] 重启进程: {process_id}")
        
        # 获取进程重启命令
        restart_info = self.ai_guardian.monitored_processes.get(process_id)
        
        if restart_info:
            # 停止旧进程
            if restart_info.get("pid"):
                try:
                    os.kill(restart_info["pid"], signal.SIGTERM)
                except Exception as e:
                    print(f"[守护进程] 停止进程失败: {e}")
            
            # 启动新进程
            process_manager = None
            try:
                from dev_bot.process_manager import ProcessManager
                process_manager = ProcessManager()
                
                process = await process_manager.create_process(
                    process_id=process_id,
                    script_path=Path(restart_info["restart_cmd"][0]),
                    args=restart_info["restart_cmd"][1:],
                    cwd=Path.cwd()
                )
                
                if process:
                    # 更新 PID
                    self.ai_guardian.monitored_processes[process_id]["pid"] = process.pid
                    print(f"[守护进程] ✓ 进程已重启: {process_id} (PID: {process.pid})")
            
            except Exception as e:
                print(f"[守护进程] 重启进程失败: {e}")
    
    async def _init_monitored_processes(self):
        """初始化要监控的进程
        
        这里注册 TUI 进程，AI 实例由守护进程启动和管理
        """
        project_root = Path.cwd()
        
        # 注册 TUI 进程（用户界面）
        tui_cmd = [
            sys.executable,
            "-m", "dev_bot"
        ]
        self.ai_guardian.register_process(
            "tui",
            None,  # 初始没有 PID
            tui_cmd,
            max_restarts=5
        )
        
        print(f"[守护进程] 已注册 TUI 进程（用户界面）")
        
        # 启动后台 AI 实例（由守护进程直接管理）
        await self._start_ai_instances(project_root)
    
    async def _start_ai_instances(self, project_root: Path):
        """启动后台 AI 实例"""
        from dev_bot.process_manager import ProcessManager
        
        process_manager = ProcessManager()
        
        # 定义 AI 实例配置
        ai_instances = {
            "ai_analyzer": {
                "script": project_root / "dev_bot" / "ai_loop_process.py",
                "args": ["--role", "analyzer"],
                "description": "AI 分析实例"
            },
            "ai_developer": {
                "script": project_root / "dev_bot" / "ai_loop_process.py",
                "args": ["--role", "developer"],
                "description": "AI 开发实例"
            },
            "ai_tester": {
                "script": project_root / "dev_bot" / "ai_loop_process.py",
                "args": ["--role", "tester"],
                "description": "AI 测试实例"
            },
            "ai_reviewer": {
                "script": project_root / "dev_bot" / "ai_loop_process.py",
                "args": ["--role", "reviewer"],
                "description": "AI 评审实例"
            }
        }
        
        print(f"[守护进程] 启动后台 AI 实例...")
        
        for instance_id, config in ai_instances.items():
            try:
                if not config["script"].exists():
                    print(f"[守护进程] 警告: 脚本不存在: {config['script']}")
                    continue
                
                process = await process_manager.create_process(
                    process_id=instance_id,
                    script_path=config["script"],
                    args=config["args"],
                    cwd=project_root,
                    use_new_session=False  # 不创建新会话，以便守护进程管理
                )
                
                if process:
                    # 注册到守护进程管理
                    restart_cmd = [
                        sys.executable,
                        str(config["script"])
                    ] + config["args"]
                    
                    self.ai_guardian.register_process(
                        instance_id,
                        process.pid,
                        restart_cmd,
                        max_restarts=10
                    )
                    
                    print(f"[守护进程] ✓ {config['description']} (PID: {process.pid})")
                else:
                    print(f"[守护进程] ✗ {config['description']} 启动失败")
            
            except Exception as e:
                print(f"[守护进程] ✗ 启动 {instance_id} 失败: {e}")
        
        print(f"[守护进程] 后台 AI 实例启动完成")
    
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
        status = custom_status or self._get_status()
        
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2, default=str)
        except Exception as e:
            print(f"[守护进程] 保存状态失败: {e}")
    
    def _get_status(self) -> Dict[str, Any]:
        """获取状态"""
        status = self.ai_guardian.get_status()
        status["pid"] = os.getpid()
        status["ipc_server"] = {
            "running": self.ipc_server is not None and self.ipc_server.is_running,
            "socket_path": str(self.ipc_socket_path),
            "clients_count": len(self.ipc_server.clients) if self.ipc_server else 0
        }
        return status
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态（公开接口）"""
        return self._get_status()
    
    def _handle_sigterm(self, signum, frame):
        """处理 SIGTERM 信号"""
        print(f"[守护进程] 收到 SIGTERM 信号，准备退出...")
        # 创建异步任务来停止守护
        asyncio.create_task(self._cleanup_and_stop())
    
    def _handle_sigint(self, signum, frame):
        """处理 SIGINT 信号"""
        print(f"[守护进程] 收到 SIGINT 信号，准备退出...")
        # 创建异步任务来停止守护
        asyncio.create_task(self._cleanup_and_stop())
    
    async def _cleanup_and_stop(self):
        """清理并停止"""
        try:
            await self.ai_guardian.stop()
            await self._stop_ipc_server()
            self._save_status({"status": "stopped"})
        except Exception as e:
            print(f"[守护进程] 清理失败: {e}")


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
