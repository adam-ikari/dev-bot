#!/usr/bin/env python3
"""Dev-Bot 守护系统 - 进程监控和健康检查"""

import asyncio
import psutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('guardian.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Guardian:
    """守护系统 - 进程管理、健康监控和 AI 智能修复"""
    
    def __init__(
        self,
        check_interval: int = 30,
        memory_threshold: int = 80,  # 80%
        cpu_threshold: int = 90,  # 90%
        disk_threshold: int = 90,  # 90%
        max_restarts: int = 5,
        restart_delay: int = 10
    ):
        self.check_interval = check_interval
        self.memory_threshold = memory_threshold
        self.cpu_threshold = cpu_threshold
        self.disk_threshold = disk_threshold
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay
        self.running = False
        self.restart_count = 0
        self.iflow = None  # AI 呼叫器
    
    def run_process(self, command: list[str]) -> None:
        """运行并监控进程（完整的进程生命周期管理）"""
        import subprocess
        import signal
        from datetime import datetime
        
        logger.info("=" * 50)
        logger.info("AI 守护系统启动")
        logger.info(f"最大重启次数: {self.max_restarts}")
        logger.info(f"重启延迟: {self.restart_delay} 秒")
        logger.info(f"检查间隔: {self.check_interval} 秒")
        logger.info("=" * 50)
        
        self.restart_count = 0
        process = None
        
        # 设置信号处理器
        def signal_handler(signum, frame):
            logger.info(f"接收到信号 {signum}")
            if process and process.poll() is None:
                logger.info("正在停止子进程...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("子进程未响应，强制终止...")
                    process.kill()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        while self.restart_count < self.max_restarts:
            attempt = self.restart_count + 1
            logger.info(f"\n启动 Dev-Bot (尝试 {attempt}/{self.max_restarts})")
            logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"命令: {' '.join(command)}")
            
            try:
                # 使用 Popen 以便更好地控制进程
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                logger.info(f"子进程 PID: {process.pid}")
                
                # 等待进程结束
                returncode = process.wait()
                
                # 正常退出，重置计数器
                if returncode == 0:
                    logger.info("Dev-Bot 正常退出")
                    self.restart_count = 0
                    break
                else:
                    logger.error(f"Dev-Bot 异常退出，返回码: {returncode}")
                    # 记录错误输出
                    if process.stdout:
                        stdout = process.stdout.read()
                        if stdout:
                            logger.error(f"stdout: {stdout}")
                    if process.stderr:
                        stderr = process.stderr.read()
                        if stderr:
                            logger.error(f"stderr: {stderr}")
                    self._handle_crash()
            
            except KeyboardInterrupt:
                logger.info("\n接收到中断信号，停止守护")
                if process and process.poll() is None:
                    process.terminate()
                break
            
            except Exception as e:
                logger.error(f"未预期的错误: {e}", exc_info=True)
                self._handle_crash()
        
        if self.restart_count >= self.max_restarts:
            logger.error(f"\n达到最大重启次数 ({self.max_restarts})，停止尝试")
            logger.error("请检查错误日志并手动解决问题")
    
    def _handle_crash(self) -> None:
        """处理崩溃 - 尝试 AI 智能修复"""
        import time
        
        self.restart_count += 1
        
        if self.restart_count < self.max_restarts:
            logger.info(f"\n🔧 尝试 AI 智能修复...")
            logger.info(f"当前重启计数: {self.restart_count}/{self.max_restarts}")
            
            # 尝试 AI 修复
            fixed = self.try_auto_fix()
            
            if fixed:
                logger.info("✅ AI 修复成功，准备重启...")
            else:
                logger.warning("⚠️ AI 修复失败，将尝试简单重启...")
            
            logger.info(f"将在 {self.restart_delay} 秒后重启...")
            time.sleep(self.restart_delay)
        else:
            logger.error("已达到最大重启次数，不再尝试")
    
    async def start(self, monitored_pid: Optional[int] = None) -> None:
        """启动守护"""
        self.running = True
        logger.info("=" * 50)
        logger.info("守护系统启动")
        logger.info(f"检查间隔: {self.check_interval} 秒")
        logger.info(f"内存阈值: {self.memory_threshold}%")
        logger.info(f"CPU 阈值: {self.cpu_threshold}%")
        logger.info(f"磁盘阈值: {self.disk_threshold}%")
        logger.info("=" * 50)
        
        if monitored_pid:
            logger.info(f"监控进程 PID: {monitored_pid}")
        else:
            logger.info("监控自身进程")
        
        try:
            while self.running:
                await self.check_health(monitored_pid)
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("守护系统已停止")
        except Exception as e:
            logger.error(f"守护系统错误: {e}")
    
    async def check_health(self, monitored_pid: Optional[int] = None) -> None:
        """检查健康状态"""
        try:
            process = psutil.Process(monitored_pid) if monitored_pid else psutil.Process()
            
            # 检查内存使用
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            if memory_percent > self.memory_threshold:
                logger.warning(f"⚠️  内存使用过高: {memory_percent:.1f}%")
            
            # 检查 CPU 使用
            cpu_percent = process.cpu_percent(interval=1)
            if cpu_percent > self.cpu_threshold:
                logger.warning(f"⚠️  CPU 使用过高: {cpu_percent:.1f}%")
            
            # 检查磁盘使用
            disk_usage = psutil.disk_usage('/')
            disk_percent = disk_usage.percent
            if disk_percent > self.disk_threshold:
                logger.warning(f"⚠️  磁盘使用过高: {disk_percent:.1f}%")
            
            # 记录健康状态
            logger.info(
                f"✅ 健康检查 - PID: {process.pid}, "
                f"内存: {memory_percent:.1f}%, "
                f"CPU: {cpu_percent:.1f}%, "
                f"磁盘: {disk_percent:.1f}%"
            )
        
        except psutil.NoSuchProcess:
            logger.error(f"❌ 进程不存在: PID {monitored_pid}")
            if monitored_pid:
                logger.info("进程已终止，守护系统停止")
                self.running = False
        
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
    
    def stop(self) -> None:
        """停止守护"""
        self.running = False
        logger.info("守护系统停止信号已发送")
    
    def try_auto_fix(self, error_context: Optional[str] = None, timeout: int = 300) -> bool:
        """尝试 AI 智能修复错误
        
        Args:
            error_context: 错误上下文信息
            timeout: AI 修复超时时间（秒），默认 300 秒（5 分钟）
        
        Returns:
            bool: 修复成功返回 True，否则返回 False
        """
        try:
            # 导入 IflowCaller
            from dev_bot.iflow import IflowCaller
            
            if self.iflow is None:
                # 设置超时参数
                self.iflow = IflowCaller(timeout=timeout)
            
            # 如果没有提供错误上下文，尝试从日志读取
            if not error_context:
                error_context = self._get_error_context()
            
            if not error_context:
                logger.warning("无法获取错误上下文，跳过 AI 修复")
                return False
            
            # 构建 AI 提示
            prompt = f"""Dev-Bot 崩溃了，请分析错误并提供修复方案。

错误信息：
{error_context}

请执行以下步骤：
1. 分析错误原因
2. 识别需要修改的文件
3. 提供具体的修复代码
4. 如果可以修复，直接使用文件操作工具修复问题

重要：
- 只修复代码错误，不要修改其他内容
- 保持代码风格一致
- 修复后返回 "FIXED: [修复描述]"
- 如果无法修复，返回 "CANNOT_FIX: [原因]"
- 修复操作应在 {timeout} 秒内完成

请开始修复。"""
            
            logger.info(f"🤖 AI 正在分析错误（超时: {timeout} 秒）...")
            
            # 调用 AI 分析（已设置超时）
            result = self.iflow.call(prompt)
            logger.info(f"AI 分析结果: {result[:200]}...")
            
            # 检查是否修复成功
            if "FIXED:" in result or "修复成功" in result or "已修复" in result:
                logger.info("✅ AI 修复成功")
                return True
            else:
                logger.warning("⚠️ AI 未能修复错误")
                return False
            
        except asyncio.TimeoutError:
            logger.error(f"AI 修复超时（{timeout} 秒）")
            return False
        except Exception as e:
            logger.error(f"AI 修复失败: {e}", exc_info=True)
            return False
    
    def _get_error_context(self) -> str:
        """获取错误上下文"""
        try:
            # 读取 supervisor.log 的最后 50 行
            supervisor_log = Path("supervisor.log")
            if supervisor_log.exists():
                with open(supervisor_log, 'r') as f:
                    lines = f.readlines()
                    return ''.join(lines[-50:])
            
            # 尝试读取 dev-bot.log
            dev_bot_log = Path("dev-bot.log")
            if dev_bot_log.exists():
                with open(dev_bot_log, 'r') as f:
                    lines = f.readlines()
                    return ''.join(lines[-50:])
            
            return ""
            
        except Exception as e:
            logger.error(f"读取错误日志失败: {e}")
            return ""
    
    async def monitor_file_changes(self, file_path: str) -> None:
        """监控文件变化"""
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return
        
        logger.info(f"监控文件变化: {file_path}")
        last_mtime = path.stat().st_mtime
        
        try:
            while self.running:
                current_mtime = path.stat().st_mtime
                if current_mtime != last_mtime:
                    logger.info(f"文件已更新: {file_path}")
                    last_mtime = current_mtime
                
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("文件监控已停止")
        except Exception as e:
            logger.error(f"文件监控失败: {e}")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dev-Bot 守护系统")
    parser.add_argument(
        "--pid",
        type=int,
        help="要监控的进程 PID (默认: 自身)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="健康检查间隔秒数 (默认: 30)"
    )
    
    args = parser.parse_args()
    
    # 创建守护
    guardian = Guardian(check_interval=args.interval)
    
    # 启动守护
    try:
        await guardian.start(args.pid)
    except KeyboardInterrupt:
        logger.info("\n接收到中断信号")
    finally:
        guardian.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)