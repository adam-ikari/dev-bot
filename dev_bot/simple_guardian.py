"""极简 AI 守护

使用 iflow 进行健康检查
"""
import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.core import get_core
from dev_bot.ipc import IPCManager
from dev_bot.output_router import get_output_router, OutputSource, LogLevel


class SimpleGuardian:
    """极简 AI 守护
    
    使用 iflow 进行健康检查
    """
    
    def __init__(
        self,
        project_root: Path,
        check_interval: int = 60
    ):
        self.project_root = project_root
        self.check_interval = check_interval
        
        self.core = get_core()
        self.ipc = IPCManager(project_root)
        self.output_router = get_output_router()
        
        self.is_running = False
        self._task = None
        
        # 监控的进程
        self.monitored_pids: Dict[str, int] = {}
        self.max_restarts = 10
        self.restart_counts: Dict[str, int] = {}
        
        # 注册信号处理
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        signal.signal(signal.SIGINT, self._handle_sigint)
    
    def register_process(
        self,
        process_name: str,
        pid: int,
        startup_command: Optional[list] = None
    ):
        """注册要监控的进程
        
        Args:
            process_name: 进程名称
            pid: 进程 PID
            startup_command: 启动命令（用于重启）
        """
        self.monitored_pids[process_name] = pid
        self.restart_counts[process_name] = 0
        
        print(f"[守护] 注册进程: {process_name}（PID: {pid}）")
    
    async def start(self):
        """启动守护"""
        if self.is_running:
            print("[守护] 已在运行")
            return
        
        self.is_running = True
        print(f"[守护] 启动极简守护（PID: {os.getpid()}）")
        print(f"[守护] 检查间隔: {self.check_interval}秒")
        print(f"[守护] 监控进程: {list(self.monitored_pids.keys())}")
        
        # 启动检查循环
        self._task = asyncio.create_task(self._check_loop())
    
    async def stop(self):
        """停止守护"""
        if not self.is_running:
            return
        
        self.is_running = False
        print("[守护] 停止极简守护")
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _check_loop(self):
        """检查循环"""
        while self.is_running:
            for process_name, pid in list(self.monitored_pids.items()):
                await self._check_process(process_name, pid)
            
            await asyncio.sleep(self.check_interval)
    
    async def _check_process(self, process_name: str, pid: int):
        """检查单个进程
        
        Args:
            process_name: 进程名称
            pid: 进程 PID
        """
        # 1. 基本存活检查
        is_alive = self._is_process_alive(pid)
        
        if not is_alive:
            print(f"[守护] 进程 {process_name}（PID: {pid}）未响应")
            
            await self.output_router.emit_guardian(
                LogLevel.ERROR,
                f"进程 {process_name}（PID: {pid}）未响应"
            )
            
            # 尝试使用 iflow 检查
            await self._iflow_health_check(process_name)
            
            return
        
        # 2. 使用 iflow 进行健康检查
        health_status = await self._iflow_health_check(process_name)
        
        if not health_status:
            print(f"[守护] 进程 {process_name}（PID: {pid}）健康检查失败")
            
            await self.output_router.emit_guardian(
                LogLevel.WARNING,
                f"进程 {process_name}（PID: {pid}）健康检查失败"
            )
        else:
            print(f"[守护] 进程 {process_name}（PID: {pid}）健康")
    
    def _is_process_alive(self, pid: int) -> bool:
        """检查进程是否存活
        
        Args:
            pid: 进程 PID
        
        Returns:
            是否存活
        """
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    async def _iflow_health_check(self, process_name: str) -> bool:
        """使用 iflow 进行健康检查
        
        Args:
            process_name: 进程名称
        
        Returns:
            是否健康
        """
        try:
            # 使用 iflow 检查进程状态
            prompt = f"""
请检查进程 {process_name} 的状态：
1. 检查进程是否正在运行
2. 检查最近的日志输出
3. 检查是否有错误
4. 返回健康状态（healthy/unhealthy）和原因
            """.strip()
            
            result = await self.core.call_iflow(prompt, timeout=30)
            
            if result["success"]:
                output = result["output"].lower()
                
                # 检查输出中是否包含 healthy
                is_healthy = "healthy" in output
                
                await self.output_router.emit_guardian(
                    LogLevel.INFO,
                    f"进程 {process_name} iflow 健康检查: {'健康' if is_healthy else '不健康'}"
                )
                
                return is_healthy
            else:
                print(f"[守护] iflow 检查失败: {result['error']}")
                return False
        
        except Exception as e:
            print(f"[守护] iflow 健康检查出错: {e}")
            return False
    
    async def restart_process(self, process_name: str):
        """重启进程
        
        Args:
            process_name: 进程名称
        """
        print(f"[守护] 尝试重启进程: {process_name}")
        
        await self.output_router.emit_guardian(
            LogLevel.WARNING,
            f"尝试重启进程: {process_name}"
        )
        
        # 检查重启次数
        restart_count = self.restart_counts.get(process_name, 0)
        
        if restart_count >= self.max_restarts:
            print(f"[守护] 进程 {process_name} 重启次数已达上限（{self.max_restarts}）")
            
            await self.output_router.emit_guardian(
                LogLevel.ERROR,
                f"进程 {process_name} 重启次数已达上限（{self.max_restarts}）"
            )
            
            return False
        
        # 使用 iflow 生成重启命令
        prompt = f"""
进程 {process_name} 需要重启。
请生成重启命令，返回命令字符串。
            """.strip()
        
        result = await self.core.call_iflow(prompt, timeout=30)
        
        if result["success"]:
            command = result["output"].strip()
            
            print(f"[守护] 执行重启命令: {command}")
            
            try:
                # 执行重启命令
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=30
                )
                
                if process.returncode == 0:
                    print(f"[守护] 进程 {process_name} 重启成功")
                    
                    await self.output_router.emit_guardian(
                        LogLevel.SUCCESS,
                        f"进程 {process_name} 重启成功"
                    )
                    
                    self.restart_counts[process_name] = restart_count + 1
                    return True
                else:
                    print(f"[守护] 进程 {process_name} 重启失败: {stderr.decode()}")
                    
                    await self.output_router.emit_guardian(
                        LogLevel.ERROR,
                        f"进程 {process_name} 重启失败"
                    )
                    
                    return False
            
            except Exception as e:
                print(f"[守护] 重启进程出错: {e}")
                return False
        else:
            print(f"[守护] 生成重启命令失败: {result['error']}")
            return False
    
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "monitored_processes": list(self.monitored_pids.keys()),
            "restart_counts": self.restart_counts
        }
    
    def _handle_sigterm(self, signum, frame):
        """处理 SIGTERM 信号"""
        print(f"[守护] 收到 SIGTERM 信号")
        self.is_running = False
    
    def _handle_sigint(self, signum, frame):
        """处理 SIGINT 信号"""
        print(f"[守护] 收到 SIGINT 信号")
        self.is_running = False


# 便捷函数
def create_guardian(project_root: Optional[Path] = None) -> SimpleGuardian:
    """创建守护实例"""
    if project_root is None:
        project_root = Path.cwd()
    
    return SimpleGuardian(project_root)


if __name__ == "__main__":
    import asyncio
    
    async def demo():
        guardian = create_guardian()
        
        # 注册一个进程
        guardian.register_process("test_process", os.getpid())
        
        # 启动守护
        await guardian.start()
        
        # 等待一段时间
        await asyncio.sleep(10)
        
        # 获取状态
        status = guardian.get_status()
        print(f"\n状态: {status}")
        
        # 停止守护
        await guardian.stop()
    
    asyncio.run(demo())