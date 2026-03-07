#!/usr/bin/env python3
"""iflow 调用器"""

import asyncio
import os
from pathlib import Path
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


class IflowTokenExpiredError(IflowError):
    """Iflow 令牌过期错误"""


class IflowMemoryError(IflowError):
    """Iflow 内存错误（WebAssembly 或堆内存不足）"""


class IflowCaller:
    """iflow 命令行工具的异步调用器"""
    
    DEFAULT_TIMEOUT = 600
    DEFAULT_MEMORY_LIMIT = 4 * 1024 * 1024 * 1024  # 4GB
    DEFAULT_NODE_MEMORY_MB = 4096  # Node.js 堆内存限制（MB）
    ALLOWED_COMMANDS = {"iflow"}  # 只允许 iflow 命令
    
    def __init__(self, command: str = "iflow", timeout: int = DEFAULT_TIMEOUT, node_memory_mb: int = DEFAULT_NODE_MEMORY_MB):
        self.command = self._validate_command(command)
        self.timeout = timeout
        self.node_memory_mb = node_memory_mb
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
        """设置资源限制（已禁用，因为会影响子进程导致 iflow WebAssembly 实例化失败）"""
        # 注意：禁用此功能，因为 resource.RLIMIT_AS 会影响所有子进程
        # 包括 iflow 进程，导致 WebAssembly 实例化时出现 "Out of memory" 错误
        # 即使设置了 4GB 的限制，iflow 的 WebAssembly 模块仍然无法正常工作
        pass
    
    async def call(self, prompt: str) -> str:
        """调用 iflow"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 设置环境变量，增加 Node.js 内存限制
            env = os.environ.copy()
            node_options = f"--max-old-space-size={self.node_memory_mb}"
            env["NODE_OPTIONS"] = node_options
            
            logger.info(f"🚀 Starting iflow process: {self.command}")
            logger.info(f"📊 Node.js memory limit: {self.node_memory_mb}MB")
            logger.info(f"⏱️  Timeout: {self.timeout}s")
            logger.info(f"📝 Prompt length: {len(prompt)} chars")
            
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                start_new_session=True if sys.platform != 'win32' else False
            )
            
            logger.info(f"✅ iflow process started: PID={self.process.pid}")
            
            self.process.stdin.write(prompt.encode())
            await self.process.stdin.drain()
            self.process.stdin.write_eof()
            
            logger.info(f"📤 Prompt sent to iflow")
            
            stdout, stderr = await asyncio.wait_for(
                self.process.communicate(),
                timeout=self.timeout
            )
            
            logger.info(f"📥 iflow process completed: returncode={self.process.returncode}")
            logger.info(f"📦 Output size: {len(stdout)} bytes, Error size: {len(stderr) if stderr else 0} bytes")
            
            if self.process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace') if stderr else "Unknown error"
                
                # 检测令牌过期错误
                token_expired_keywords = [
                    "token expired",
                    "authentication failed",
                    "unauthorized",
                    "401",
                    "token invalid",
                    "token refresh",
                    "access token expired"
                ]
                
                # 检测内存错误（WebAssembly 或堆内存不足）
                memory_error_keywords = [
                    "RangeError: WebAssembly",
                    "WebAssembly.instantiate",
                    "out of memory",
                    "JavaScript heap out of memory",
                    "ENOMEM",
                    "Cannot allocate memory",
                    "memory limit",
                    "insufficient memory"
                ]
                
                error_msg_lower = error_msg.lower()
                
                if any(keyword in error_msg_lower for keyword in token_expired_keywords):
                    raise IflowTokenExpiredError(
                        f"iflow token expired: {error_msg}. "
                        f"Please re-run 'iflow auth' to refresh your token."
                    )
                
                if any(keyword in error_msg_lower for keyword in memory_error_keywords):
                    raise IflowMemoryError(
                        f"iflow memory error: {error_msg}. "
                        f"System or iflow process has insufficient memory. "
                        f"Node.js memory limit is set to {self.node_memory_mb}MB. "
                        f"Try: 1) Close other applications, 2) Increase Node.js memory limit, 3) Increase system memory."
                    )
                
                raise IflowProcessError(f"iflow exited with code {self.process.returncode}: {error_msg}")
            
            result = stdout.decode('utf-8', errors='replace')
            logger.info(f"✅ iflow call successful: output length={len(result)} chars")
            return result
        except asyncio.TimeoutError:
            logger.error(f"⏰ iflow timeout after {self.timeout} seconds")
            self.stop()
            raise IflowTimeoutError(f"iflow timed out after {self.timeout} seconds")
        except IflowError as e:
            logger.error(f"❌ iflow error: {type(e).__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected iflow error: {type(e).__name__}: {e}", exc_info=True)
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
    
    @staticmethod
    def check_availability() -> tuple[bool, str]:
        """检查 iflow 是否可用
        
        Returns:
            tuple: (是否可用, 详细信息)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 检查 iflow 命令是否存在
            resolved = shutil.which("iflow")
            if not resolved:
                return False, "iflow 命令未找到，请先安装 iflow"
            
            logger.info(f"✅ iflow 命令已找到: {resolved}")
            
            # 检查 iflow 是否可执行
            if not os.access(resolved, os.X_OK):
                return False, f"iflow 文件不可执行: {resolved}"
            
            logger.info(f"✅ iflow 可执行")
            
            # 检查 Node.js 版本
            node_path = shutil.which("node")
            if not node_path:
                return False, "Node.js 未找到，iflow 需要 Node.js 环境"
            
            logger.info(f"✅ Node.js 已找到: {node_path}")
            
            # 检查系统内存
            try:
                import psutil
                mem = psutil.virtual_memory()
                total_gb = mem.total / (1024**3)
                available_gb = mem.available / (1024**3)
                
                logger.info(f"📊 系统内存: 总计 {total_gb:.1f}GB, 可用 {available_gb:.1f}GB")
                
                if available_gb < 1.0:
                    logger.warning(f"⚠️ 可用内存不足 1GB，可能影响 iflow 运行")
                
            except ImportError:
                logger.warning("⚠️ psutil 未安装，无法检查系统内存")
            
            # 尝试简单测试 iflow 命令
            import subprocess
            try:
                result = subprocess.run(
                    [resolved, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    logger.info(f"✅ iflow 版本: {result.stdout.strip()}")
                    return True, f"iflow 可用: {result.stdout.strip()}"
                else:
                    logger.warning(f"⚠️ iflow --version 返回错误: {result.stderr}")
                    return True, f"iflow 命令存在但版本检查失败"
                    
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ iflow --version 超时")
                return True, f"iflow 命令存在但响应超时"
            except FileNotFoundError:
                return False, f"iflow 文件未找到: {resolved}"
            except Exception as e:
                logger.warning(f"⚠️ iflow 测试失败: {e}")
                return True, f"iflow 命令存在但测试失败: {e}"
                
        except Exception as e:
            logger.error(f"❌ 检查 iflow 可用性失败: {e}")
            return False, f"检查失败: {e}"