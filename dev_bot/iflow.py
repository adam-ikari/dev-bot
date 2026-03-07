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
    
    SAFE_COMMANDS = ["iflow", "/usr/bin/iflow", shutil.which("iflow") or "iflow"]
    DEFAULT_TIMEOUT = 600
    DEFAULT_MEMORY_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB
    
    def __init__(self, command: str = "iflow", timeout: int = DEFAULT_TIMEOUT):
        self._validate_command(command)
        self.command = command
        self.timeout = timeout
        self.process = None
        self._set_resource_limits()
    
    def _validate_command(self, command: str) -> None:
        """验证命令安全性"""
        if not command:
            raise ValueError("Command cannot be empty")
        
        if command not in self.SAFE_COMMANDS:
            raise ValueError(f"Unsafe command: {command}. Allowed: {self.SAFE_COMMANDS}")
    
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