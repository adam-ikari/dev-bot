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
    """守护系统 - 监控进程健康"""
    
    def __init__(
        self,
        check_interval: int = 30,
        memory_threshold: int = 80,  # 80%
        cpu_threshold: int = 90,  # 90%
        disk_threshold: int = 90  # 90%
    ):
        self.check_interval = check_interval
        self.memory_threshold = memory_threshold
        self.cpu_threshold = cpu_threshold
        self.disk_threshold = disk_threshold
        self.running = False
    
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