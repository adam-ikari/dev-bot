#!/usr/bin/env python3
"""iflow 调用器"""

import asyncio
import logging
import os
from pathlib import Path
import sys
import signal as signal_module
import resource
import shutil

logger = logging.getLogger(__name__)


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
    DEFAULT_NODE_MEMORY_MB = 0  # Node.js 堆内存限制（MB），0 表示不限制
    ALLOWED_COMMANDS = {"iflow"}  # 只允许 iflow 命令

    # 热重载指令标识符
    HOT_RELOAD_COMMANDS = [
        "RELOAD_PROMPT",
        "HOT_RELOAD",
        "重新加载提示词",
        "reload prompt",
        "reload the prompt"
    ]

    def __init__(self, command: str = "iflow", timeout: int = None, node_memory_mb: int = None, hot_reload_callback=None):
        """初始化 IflowCaller

        Args:
            command: iflow 命令路径
            timeout: 超时时间（秒）
            node_memory_mb: Node.js 内存限制（MB）
            hot_reload_callback: 热重载回调函数
        """
        self.command = self._validate_command(command)
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.node_memory_mb = node_memory_mb if node_memory_mb is not None else self.DEFAULT_NODE_MEMORY_MB
        self.process = None
        self.hot_reload_callback = hot_reload_callback
        self._set_resource_limits()

    def _validate_command(self, command: str) -> str:
        """验证命令安全性"""
        if not command:
            raise ValueError("Command cannot be empty")

        if os.path.isabs(command):
            if not os.path.exists(command):
                raise ValueError(f"Command not found: {command}")
            command_path = Path(command)
        else:
            resolved = shutil.which(command)
            if not resolved:
                raise ValueError(f"Command not found in PATH: {command}")
            command_path = Path(resolved)

        if command_path.name not in self.ALLOWED_COMMANDS:
            raise ValueError(
                f"Unsafe command: {command}. "
                f"Allowed commands: {', '.join(self.ALLOWED_COMMANDS)}"
            )

        if not os.access(command_path, os.X_OK):
            raise ValueError(f"Command is not executable: {command_path}")

        return str(command_path.absolute())

    def _set_resource_limits(self) -> None:
        """设置资源限制（已禁用）"""
        pass

    async def call(self, prompt: str) -> str:
        """调用 iflow（每次创建新进程）

        Args:
            prompt: 提示词

        Returns:
            iflow 响应
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            env = os.environ.copy()
            if self.node_memory_mb > 0:
                node_options = f"--max-old-space-size={self.node_memory_mb}"
                env["NODE_OPTIONS"] = node_options
                logger.info(f"📊 Node.js memory limit: {self.node_memory_mb}MB")
            else:
                logger.info(f"📊 Node.js memory limit: unlimited")

            logger.info(f"🚀 Starting iflow process: {self.command}")
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

                token_expired_keywords = [
                    "token expired", "authentication failed", "unauthorized",
                    "401", "token invalid", "token refresh", "access token expired"
                ]

                memory_error_keywords = [
                    "RangeError: WebAssembly", "WebAssembly.instantiate",
                    "out of memory", "JavaScript heap out of memory",
                    "ENOMEM", "Cannot allocate memory", "memory limit"
                ]

                error_msg_lower = error_msg.lower()

                if any(keyword in error_msg_lower for keyword in token_expired_keywords):
                    raise IflowTokenExpiredError(
                        f"iflow token expired: {error_msg}. "
                        f"Please re-run 'iflow auth' to refresh your token."
                    )

                if any(keyword in error_msg_lower for keyword in memory_error_keywords):
                    memory_limit_info = f"Node.js memory limit is set to {self.node_memory_mb}MB." if self.node_memory_mb > 0 else "Node.js memory limit is unlimited."
                    raise IflowMemoryError(
                        f"iflow memory error: {error_msg}. "
                        f"System or iflow process has insufficient memory. "
                        f"{memory_limit_info} "
                        f"Try: 1) Close other applications, 2) Increase system memory."
                    )

                raise IflowProcessError(f"iflow exited with code {self.process.returncode}: {error_msg}")

            result = stdout.decode('utf-8', errors='replace')
            logger.info(f"✅ iflow call successful: output length={len(result)} chars")

            # 检测热重载指令
            if self._detect_hot_reload_command(result):
                logger.info("🔄 检测到热重载指令，触发回调...")
                if self.hot_reload_callback:
                    self.hot_reload_callback()

            return result

        except asyncio.TimeoutError:
            logger.error(f"iflow process timeout after {self.timeout}s")
            raise IflowTimeoutError(f"iflow timeout after {self.timeout}s")

    def _detect_hot_reload_command(self, text: str) -> bool:
        """检测文本中是否包含热重载指令"""
        text_lower = text.lower()
        for command in self.HOT_RELOAD_COMMANDS:
            if command.lower() in text_lower:
                logger.info(f"检测到热重载指令: {command}")
                return True
        return False

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


class IflowSession:
    """持久的 iflow 会话，用于在同一个进程中持续对话"""

    def __init__(self, command: str = "iflow", timeout: int = 600, node_memory_mb: int = 0):
        self.command = self._validate_command(command)
        self.timeout = timeout
        self.node_memory_mb = node_memory_mb
        self.process = None
        self.session_active = False
        self._set_resource_limits()

    def _validate_command(self, command: str) -> str:
        """验证命令安全性"""
        if not command:
            raise ValueError("Command cannot be empty")

        if os.path.isabs(command):
            if not os.path.exists(command):
                raise ValueError(f"Command not found: {command}")
            command_path = Path(command)
        else:
            resolved = shutil.which(command)
            if not resolved:
                raise ValueError(f"Command not found in PATH: {command}")
            command_path = Path(resolved)

        if command_path.name not in IflowCaller.ALLOWED_COMMANDS:
            raise ValueError(
                f"Unsafe command: {command}. "
                f"Allowed commands: {', '.join(IflowCaller.ALLOWED_COMMANDS)}"
            )

        if not os.access(command_path, os.X_OK):
            raise ValueError(f"Command is not executable: {command_path}")

        return str(command_path.absolute())

    def _set_resource_limits(self) -> None:
        """设置资源限制（已禁用）"""
        pass

    async def start(self) -> None:
        """启动 iflow 会话"""
        if self.session_active:
            logger.warning("Session already active")
            return

        try:
            env = os.environ.copy()
            if self.node_memory_mb > 0:
                node_options = f"--max-old-space-size={self.node_memory_mb}"
                env["NODE_OPTIONS"] = node_options
                logger.info(f"📊 Node.js memory limit: {self.node_memory_mb}MB")
            else:
                logger.info(f"📊 Node.js memory limit: unlimited")

            logger.info(f"🚀 Starting iflow session: {self.command}")
            logger.info(f"⏱️  Timeout: {self.timeout}s")

            self.process = await asyncio.create_subprocess_exec(
                self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                start_new_session=True if sys.platform != 'win32' else False
            )

            logger.info(f"✅ iflow session started: PID={self.process.pid}")
            self.session_active = True

        except Exception as e:
            logger.error(f"Failed to start iflow session: {e}")
            raise

    async def send(self, prompt: str) -> str:
        """发送提示词到 iflow 会话并获取响应

        Args:
            prompt: 提示词

        Returns:
            iflow 响应
        """
        if not self.session_active or not self.process:
            raise IflowError("Session not active. Call start() first.")

        try:
            logger.info(f"📤 Sending prompt to iflow ({len(prompt)} chars)")

            # 发送提示词
            self.process.stdin.write(prompt.encode())
            await self.process.stdin.drain()
            self.process.stdin.write_eof()

            # 等待响应
            stdout, stderr = await asyncio.wait_for(
                self.process.communicate(),
                timeout=self.timeout
            )

            logger.info(f"📥 iflow response received")
            logger.info(f"📦 Output size: {len(stdout)} bytes, Error size: {len(stderr) if stderr else 0} bytes")

            if self.process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace') if stderr else "Unknown error"

                # 检测令牌过期
                token_expired_keywords = [
                    "token expired", "authentication failed", "unauthorized",
                    "401", "token invalid", "token refresh", "access token expired"
                ]

                # 检测内存错误
                memory_error_keywords = [
                    "RangeError: WebAssembly", "WebAssembly.instantiate",
                    "out of memory", "JavaScript heap out of memory",
                    "ENOMEM", "Cannot allocate memory", "memory limit"
                ]

                error_msg_lower = error_msg.lower()

                if any(keyword in error_msg_lower for keyword in token_expired_keywords):
                    raise IflowTokenExpiredError(
                        f"iflow token expired: {error_msg}. "
                        f"Please re-run 'iflow auth' to refresh your token."
                    )

                if any(keyword in error_msg_lower for keyword in memory_error_keywords):
                    memory_limit_info = f"Node.js memory limit is set to {self.node_memory_mb}MB." if self.node_memory_mb > 0 else "Node.js memory limit is unlimited."
                    raise IflowMemoryError(
                        f"iflow memory error: {error_msg}. "
                        f"System or iflow process has insufficient memory. "
                        f"{memory_limit_info} "
                        f"Try: 1) Close other applications, 2) Increase system memory."
                    )

                raise IflowProcessError(f"iflow exited with code {self.process.returncode}: {error_msg}")

            result = stdout.decode('utf-8', errors='replace')
            logger.info(f"✅ iflow call successful: output length={len(result)} chars")

            # 会话结束后标记为不活跃
            self.session_active = False

            return result

        except asyncio.TimeoutError:
            logger.error(f"iflow session timeout after {self.timeout}s")
            raise IflowTimeoutError(f"iflow timeout after {self.timeout}s")

    async def stop(self) -> None:
        """停止 iflow 会话"""
        if not self.session_active or not self.process:
            return

        try:
            logger.info("🛑 Stopping iflow session...")

            if sys.platform != 'win32':
                # 发送 SIGTERM 到进程组
                try:
                    import signal
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                except (ProcessLookupError, OSError):
                    pass

            # 等待进程结束
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("iflow session did not exit gracefully, forcing kill")
                if sys.platform != 'win32':
                    try:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    except (ProcessLookupError, OSError):
                        pass
                self.process.kill()
                await self.process.wait()

            logger.info("✅ iflow session stopped")

        except Exception as e:
            logger.error(f"Error stopping iflow session: {e}")
        finally:
            self.session_active = False
            self.process = None

    # 热重载指令标识符
    HOT_RELOAD_COMMANDS = [
        "RELOAD_PROMPT",
        "HOT_RELOAD",
        "重新加载提示词",
        "reload prompt",
        "reload the prompt"
    ]

    def __init__(self, command: str = "iflow", timeout: int = None, node_memory_mb: int = None, hot_reload_callback=None):
        self.command = self._validate_command(command)
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        self.node_memory_mb = node_memory_mb if node_memory_mb is not None else self.DEFAULT_NODE_MEMORY_MB
        self.process = None
        self.hot_reload_callback = hot_reload_callback  # 热重载回调函数
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
            # 设置环境变量，仅在内存限制大于 0 时才设置 Node.js 内存限制
            env = os.environ.copy()
            if self.node_memory_mb > 0:
                node_options = f"--max-old-space-size={self.node_memory_mb}"
                env["NODE_OPTIONS"] = node_options
                logger.info(f"📊 Node.js memory limit: {self.node_memory_mb}MB")
            else:
                logger.info(f"📊 Node.js memory limit: unlimited")

            logger.info(f"🚀 Starting iflow process: {self.command}")
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
                    memory_limit_info = f"Node.js memory limit is set to {self.node_memory_mb}MB." if self.node_memory_mb > 0 else "Node.js memory limit is unlimited."
                    raise IflowMemoryError(
                        f"iflow memory error: {error_msg}. "
                        f"System or iflow process has insufficient memory. "
                        f"{memory_limit_info} "
                        f"Try: 1) Close other applications, 2) Increase system memory."
                    )
                
                raise IflowProcessError(f"iflow exited with code {self.process.returncode}: {error_msg}")
            
            result = stdout.decode('utf-8', errors='replace')
            logger.info(f"✅ iflow call successful: output length={len(result)} chars")
            
            # 检测热重载指令
            if self._detect_hot_reload_command(result):
                logger.info("🔄 检测到热重载指令，触发回调...")
                if self.hot_reload_callback:
                    self.hot_reload_callback()
            
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
    
    def _detect_hot_reload_command(self, text: str) -> bool:
        """检测文本中是否包含热重载指令
        
        Args:
            text: 要检测的文本
            
        Returns:
            bool: 如果检测到热重载指令返回 True，否则返回 False
        """
        text_lower = text.lower()
        for command in self.HOT_RELOAD_COMMANDS:
            if command.lower() in text_lower:
                logger.info(f"检测到热重载指令: {command}")
                return True
        return False
    
    async def __aenter__(self):
        return self
    
