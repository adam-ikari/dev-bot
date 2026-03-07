#!/usr/bin/env python3
"""Dev-Bot 监督器 - 自动重启和进程管理"""

import subprocess
import time
import logging
import sys
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('supervisor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DevBotSupervisor:
    """Dev-Bot 监督器 - 进程管理和重启"""
    
    def __init__(self, max_restarts: int = 5, restart_delay: int = 10):
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay
        self.restart_count = 0
        self.log_file = Path("supervisor.log")
        self.guardian = None  # 守护系统
    
    def run(self, command: list[str]) -> None:
        """运行并监控 Dev-Bot"""
        logger.info("=" * 50)
        logger.info("Dev-Bot 监督器启动")
        logger.info(f"最大重启次数: {self.max_restarts}")
        logger.info(f"重启延迟: {self.restart_delay} 秒")
        logger.info("✅ 守护系统已启用")
        logger.info("=" * 50)
        
        while self.restart_count < self.max_restarts:
            attempt = self.restart_count + 1
            logger.info(f"\n启动 Dev-Bot (尝试 {attempt}/{self.max_restarts})")
            logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            try:
                # 运行 Dev-Bot
                result = subprocess.run(
                    command,
                    check=True,
                    capture_output=False
                )
                
                # 正常退出，重置计数器
                if result.returncode == 0:
                    logger.info("Dev-Bot 正常退出")
                    self.restart_count = 0
                    break
                else:
                    logger.error(f"Dev-Bot 异常退出，返回码: {result.returncode}")
                    self._handle_crash()
            
            except subprocess.CalledProcessError as e:
                logger.error(f"Dev-Bot 崩溃: {e}")
                self._handle_crash()
            
            except KeyboardInterrupt:
                logger.info("\n接收到中断信号，停止监督器")
                break
            
            except Exception as e:
                logger.error(f"未预期的错误: {e}")
                self._handle_crash()
        
        if self.restart_count >= self.max_restarts:
            logger.error(f"\n达到最大重启次数 ({self.max_restarts})，停止尝试")
            logger.error("请检查错误日志并手动解决问题")
    
    def _handle_crash(self) -> None:
        """处理崩溃 - 调用守护系统尝试修复"""
        self.restart_count += 1
        
        if self.restart_count < self.max_restarts:
            logger.info(f"\n🔧 调用守护系统尝试修复...")
            logger.info(f"当前重启计数: {self.restart_count}/{self.max_restarts}")
            
            # 尝试守护系统修复
            fixed = self._call_guardian_fix()
            
            if fixed:
                logger.info("✅ 守护系统修复成功，准备重启...")
            else:
                logger.warning("⚠️ 守护系统修复失败，将尝试简单重启...")
            
            logger.info(f"将在 {self.restart_delay} 秒后重启...")
            time.sleep(self.restart_delay)
        else:
            logger.error("已达到最大重启次数，不再尝试")
    
    def _call_guardian_fix(self) -> bool:
        """调用守护系统尝试修复"""
        try:
            # 导入 Guardian
            from dev_bot.guardian import Guardian
            
            if self.guardian is None:
                self.guardian = Guardian()
            
            # 调用守护系统的修复方法
            return self.guardian.try_auto_fix()
            
        except Exception as e:
            logger.error(f"调用守护系统失败: {e}")
            return False
    
    def check_dependencies(self) -> bool:
        """检查依赖"""
        try:
            import dev_bot
            logger.info("✅ dev_bot 模块可用")
            return True
        except ImportError:
            logger.error("❌ dev_bot 模块不可用")
            logger.error("请先安装依赖: uv pip install -e .")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Dev-Bot - AI 驱动的自主开发工具（所有模式都带自动重启）"
    )
    
    # 模式选择
    parser.add_argument(
        "mode",
        choices=["tui", "headless"],
        nargs="?",
        default="tui",
        help="运行模式：tui（终端界面，默认）或 headless（无头模式）"
    )
    
    parser.add_argument(
        "--max-restarts",
        type=int,
        default=5,
        help="最大重启次数 (默认: 5)"
    )
    parser.add_argument(
        "--restart-delay",
        type=int,
        default=10,
        help="重启延迟秒数 (默认: 10)"
    )
    
    args = parser.parse_args()
    
    # 根据模式选择命令
    if args.mode == "tui":
        command = ["python", "-m", "dev_bot.tui"]
        mode_name = "TUI"
    else:  # headless
        command = ["python", "-m", "dev_bot.__main__"]
        mode_name = "无头模式"
    
    # 创建监督器
    supervisor = DevBotSupervisor(
        max_restarts=args.max_restarts,
        restart_delay=args.restart_delay
    )
    
    # 检查依赖
    if not supervisor.check_dependencies():
        sys.exit(1)
    
    # 运行监督器
    try:
        supervisor.run(command)
    except KeyboardInterrupt:
        logger.info("\n监督器已停止")
        sys.exit(0)


if __name__ == "__main__":
    main()