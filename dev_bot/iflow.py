#!/usr/bin/env python3
"""iflow 调用器"""

import asyncio
import sys
import signal as signal_module
import resource
import shutil


class IflowError(Exception):
    """Iflow 操作错误基类"""


class IflowTimeoutError(IflowError):
    """Iflow 超时错误"""


class IflowProcessError(IflowError):
    """Iflow 进程错误"""


class IflowCaller:
    """iflow 命令行工具的异步调用器"""
    
    DEFAULT_TIMEOUT = 600
    DEFAULT_MEMORY_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB
    ALLOWED_COMMANDS = {"iflow"}  # 只允许 iflow 命令
    
    def __init__(self, command: str = "iflow", timeout: int = DEFAULT_TIMEOUT):
        self.command = self._validate_command(command)
        self.timeout = timeout
        self.process = None
        self._set_resource_limits()
    
    def _validate_command(self, command: str) -> str:
        """验证命令安全性，返回解析后的绝对路径"""
        if not command:
            raise ValueError("Command cannot be empty")
        
        # 解析命令路径
        if os.path.isabs(command):
            # 绝对路径：检查文件是否存在且可执行
            if not os.path.exists(command):
                raise ValueError(f"Command not found: {command}")
            command_path = Path(command)
        else:
            # 相对路径：在 PATH 中查找
            resolved = shutil.which(command)
            if not resolved:
                raise ValueError(f"Command not found in PATH: {command}")
            command_path = Path(resolved)
        
        # 白名单验证（只允许 iflow）
        if command_path.name not in self.ALLOWED_COMMANDS:
            raise ValueError(
                f"Unsafe command: {command}. "
                f"Allowed commands: {', '.join(self.ALLOWED_COMMANDS)}"
            )
        
        # 验证可执行权限
        if not os.access(command_path, os.X_OK):
            raise ValueError(f"Command is not executable: {command_path}")
        
        # 返回绝对路径
        return str(command_path.absolute())
    
    def _set_resource_limits(self) -> None:
        """设置资源限制"""
        try:
            resource.setrlimit(resource.RLIMIT_AS, (self.DEFAULT_MEMORY_LIMIT, resource.RLIM_INFINITY))
        except (ValueError, resource.error):
            pass  # 某些环境可能不支持
    
    async def call(self, prompt: str) -> str:
        """调用 iflow"""
        try:
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True if sys.platform != 'win32' else False
            )
            self.process.stdin.write(prompt.encode())
            await self.process.stdin.drain()
            self.process.stdin.write_eof()
            
            stdout, stderr = await asyncio.wait_for(
                self.process.communicate(),
                timeout=self.timeout
            )
            
            if self.process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace') if stderr else "Unknown error"
                raise IflowProcessError(f"iflow exited with code {self.process.returncode}: {error_msg}")
            
            return stdout.decode('utf-8', errors='replace')
        except asyncio.TimeoutError:
            self.stop()
            raise IflowTimeoutError(f"iflow timed out after {self.timeout} seconds")
        except IflowError:
            raise
        except Exception as e:
            raise IflowError(f"Unexpected error: {e}")
    
    def stop(self) -> None:
        """停止进程"""
        if self.process:
            try:
                if sys.platform != 'win32':
                    import os
                    try:
                        pgid = os.getpgid(self.process.pid)
                        os.killpg(pgid, signal_module.SIGTERM)
                        self.process.wait(timeout=2.0)
                    except (ProcessLookupError, Exception):
                        pass
                    try:
                        pgid = os.getpgid(self.process.pid)
                        os.killpg(pgid, signal_module.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    self.process.kill()
            except Exception:
                pass
            finally:
                self.process = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.stop()