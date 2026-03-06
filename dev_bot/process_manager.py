#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理工具

提供统一的进程创建和管理接口，避免直接使用 python3 命令
使用 sys.executable 获取当前 Python 解释器路径
"""

import asyncio
import os
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple


class ProcessManager:
    """进程管理器
    
    提供统一的进程创建和管理接口
    """
    
    def __init__(self):
        self.processes: Dict[str, asyncio.subprocess.Process] = {}
        self.current_python = sys.executable
    
    def get_python_interpreter(self) -> str:
        """获取当前 Python 解释器路径"""
        return self.current_python
    
    async def create_process(
        self,
        process_id: str,
        script_path: Path,
        args: List[str],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        use_new_session: bool = True
    ) -> Optional[asyncio.subprocess.Process]:
        """创建一个子进程
        
        Args:
            process_id: 进程唯一标识
            script_path: 要执行的脚本路径
            args: 传递给脚本的参数列表
            cwd: 工作目录（默认为脚本所在目录）
            env: 环境变量（默认继承父进程环境）
            use_new_session: 是否创建新会话（默认 True）
        
        Returns:
            创建的进程对象，失败返回 None
        """
        try:
            # 构建命令
            cmd = [self.current_python, str(script_path)] + args
            
            # 确定工作目录
            work_dir = cwd or script_path.parent
            
            # 确定环境变量
            process_env = env if env is not None else os.environ.copy()
            
            # 创建进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(work_dir),
                env=process_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=use_new_session
            )
            
            # 保存进程引用
            self.processes[process_id] = process
            
            return process
            
        except Exception as e:
            print(f"[进程管理器] 创建进程失败 ({process_id}): {e}")
            return None
    
    async def create_ai_process(
        self,
        process_id: str,
        project_root: Path,
        config_file: str = "config.json"
    ) -> Optional[asyncio.subprocess.Process]:
        """创建 AI 循环进程
        
        Args:
            process_id: 进程唯一标识
            project_root: 项目根目录
            config_file: 配置文件名
        
        Returns:
            创建的进程对象
        """
        script_path = project_root / "dev_bot" / "ai_loop_process.py"
        args = [str(project_root), config_file]
        
        return await self.create_process(
            process_id=process_id,
            script_path=script_path,
            args=args,
            cwd=project_root
        )
    
    async def create_guardian_process(
        self,
        process_id: str,
        project_root: Path,
        check_interval: int = 30,
        config_file: Optional[Path] = None
    ) -> Optional[asyncio.subprocess.Process]:
        """创建守护进程
        
        Args:
            process_id: 进程唯一标识
            project_root: 项目根目录
            check_interval: 检查间隔（秒）
            config_file: 配置文件路径（可选）
        
        Returns:
            创建的进程对象
        """
        script_path = project_root / "dev_bot" / "guardian_process.py"
        args = ["standalone", str(check_interval)]
        
        if config_file:
            args.append(str(config_file))
        
        return await self.create_process(
            process_id=process_id,
            script_path=script_path,
            args=args,
            cwd=project_root
        )
    
    async def create_tui_process(
        self,
        process_id: str,
        project_root: Path
    ) -> Optional[asyncio.subprocess.Process]:
        """创建 TUI 进程
        
        Args:
            process_id: 进程唯一标识
            project_root: 项目根目录
        
        Returns:
            创建的进程对象
        """
        script_path = project_root / "dev_bot" / "process_coordinator.py"
        args = []
        
        return await self.create_process(
            process_id=process_id,
            script_path=script_path,
            args=args,
            cwd=project_root
        )
    
    def get_process(self, process_id: str) -> Optional[asyncio.subprocess.Process]:
        """获取进程对象
        
        Args:
            process_id: 进程唯一标识
        
        Returns:
            进程对象，不存在返回 None
        """
        return self.processes.get(process_id)
    
    def is_process_running(self, process_id: str) -> bool:
        """检查进程是否在运行
        
        Args:
            process_id: 进程唯一标识
        
        Returns:
            进程是否在运行
        """
        process = self.get_process(process_id)
        if not process:
            return False
        
        return process.returncode is None
    
    def get_process_pid(self, process_id: str) -> Optional[int]:
        """获取进程 PID
        
        Args:
            process_id: 进程唯一标识
        
        Returns:
            进程 PID，不存在返回 None
        """
        process = self.get_process(process_id)
        if not process:
            return None
        
        return process.pid
    
    async def stop_process(
        self,
        process_id: str,
        timeout: float = 10.0,
        force: bool = False
    ) -> bool:
        """停止进程
        
        Args:
            process_id: 进程唯一标识
            timeout: 等待超时时间（秒）
            force: 是否强制终止
        
        Returns:
            是否成功停止
        """
        process = self.get_process(process_id)
        if not process:
            return False
        
        try:
            pid = process.pid
            if not pid:
                return False
            
            # 发送 SIGTERM
            os.kill(pid, signal.SIGTERM)
            
            # 等待进程退出
            try:
                await asyncio.wait_for(process.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                # 超时，强制终止
                if force:
                    os.kill(pid, signal.SIGKILL)
                    await process.wait()
                else:
                    return False
            
            # 从管理器中移除
            del self.processes[process_id]
            
            return True
            
        except ProcessLookupError:
            # 进程已不存在
            if process_id in self.processes:
                del self.processes[process_id]
            return True
        except Exception as e:
            print(f"[进程管理器] 停止进程失败 ({process_id}): {e}")
            return False
    
    async def stop_all_processes(self, timeout: float = 10.0) -> Dict[str, bool]:
        """停止所有进程
        
        Args:
            timeout: 等待超时时间（秒）
        
        Returns:
            每个进程的停止结果
        """
        results = {}
        
        # 复制进程 ID 列表，避免在迭代时修改字典
        process_ids = list(self.processes.keys())
        
        for process_id in process_ids:
            results[process_id] = await self.stop_process(process_id, timeout)
        
        return results
    
    def get_all_process_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有进程信息
        
        Returns:
            进程信息字典
        """
        info = {}
        
        for process_id, process in self.processes.items():
            info[process_id] = {
                "pid": process.pid,
                "running": process.returncode is None,
                "returncode": process.returncode
            }
        
        return info
    
    def get_running_process_count(self) -> int:
        """获取运行中的进程数量"""
        return sum(1 for p in self.processes.values() if p.returncode is None)
    
    def cleanup_finished_processes(self) -> int:
        """清理已完成的进程
        
        Returns:
            清理的进程数量
        """
        finished_ids = [
            pid for pid, process in self.processes.items()
            if process.returncode is not None
        ]
        
        for pid in finished_ids:
            del self.processes[pid]
        
        return len(finished_ids)


# 全局进程管理器实例
_global_process_manager = None


def get_process_manager() -> ProcessManager:
    """获取全局进程管理器实例
    
    Returns:
        全局进程管理器实例
    """
    global _global_process_manager
    
    if _global_process_manager is None:
        _global_process_manager = ProcessManager()
    
    return _global_process_manager


def reset_process_manager():
    """重置全局进程管理器（主要用于测试）"""
    global _global_process_manager
    _global_process_manager = None


# 便捷函数
async def start_ai_loop(
    project_root: Path,
    config_file: str = "config.json",
    process_id: str = "ai_loop"
) -> Optional[int]:
    """便捷函数：启动 AI 循环
    
    Args:
        project_root: 项目根目录
        config_file: 配置文件名
        process_id: 进程 ID
    
    Returns:
        进程 PID，失败返回 None
    """
    manager = get_process_manager()
    process = await manager.create_ai_process(process_id, project_root, config_file)
    
    return process.pid if process else None


async def stop_ai_loop(
    process_id: str = "ai_loop",
    timeout: float = 10.0
) -> bool:
    """便捷函数：停止 AI 循环
    
    Args:
        process_id: 进程 ID
        timeout: 超时时间
    
    Returns:
        是否成功停止
    """
    manager = get_process_manager()
    return await manager.stop_process(process_id, timeout)


async def start_guardian(
    project_root: Path,
    check_interval: int = 30,
    config_file: Optional[Path] = None,
    process_id: str = "guardian"
) -> Optional[int]:
    """便捷函数：启动守护进程
    
    Args:
        project_root: 项目根目录
        check_interval: 检查间隔
        config_file: 配置文件路径
        process_id: 进程 ID
    
    Returns:
        进程 PID，失败返回 None
    """
    manager = get_process_manager()
    process = await manager.create_guardian_process(
        process_id, project_root, check_interval, config_file
    )
    
    return process.pid if process else None


async def stop_guardian(
    process_id: str = "guardian",
    timeout: float = 10.0
) -> bool:
    """便捷函数：停止守护进程
    
    Args:
        process_id: 进程 ID
        timeout: 超时时间
    
    Returns:
        是否成功停止
    """
    manager = get_process_manager()
    return await manager.stop_process(process_id, timeout)