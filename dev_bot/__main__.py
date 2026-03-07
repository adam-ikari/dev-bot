#!/usr/bin/env python3
"""AI 自循环（命令行版本）- 由 Guardian 统一管理"""

import asyncio
import os
import sys
import signal as signal_module
import logging

from dev_bot.guardian import Guardian

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dev-bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def setup_signal_handlers(guardian_instance):
    """设置信号处理器"""
    def signal_handler(signum, frame):
        logger.info(f"接收到信号 {signum}，正在停止...")
        asyncio.create_task(guardian_instance.stop_ai_loop())
        sys.exit(0)
    
    signal_module.signal(signal_module.SIGTERM, signal_handler)
    signal_module.signal(signal_module.SIGINT, signal_handler)


async def main_async():
    """AI 自循环（异步版本）- 由 Guardian 统一管理"""
    # 创建 Guardian 实例（所有 AI 进程的统一管理器）
    try:
        loop_interval_str = os.getenv('DEVBOT_LOOP_INTERVAL', '1')
        loop_interval = int(loop_interval_str) if loop_interval_str.isdigit() else 1
        loop_interval = max(1, min(loop_interval, 300))  # 限制在 1-300 秒
    except Exception as e:
        logger.warning(f"解析循环间隔失败: {e}，使用默认值 1 秒")
        loop_interval = 1
    
    guardian = Guardian(ai_loop_interval=loop_interval)
    setup_signal_handlers(guardian)
    
    logger.info("Dev-Bot 启动（命令行模式）")
    logger.info(f"循环间隔: {loop_interval} 秒")
    logger.info("AI 循环由 Guardian 统一管理")
    logger.info("提示: 使用 'dev-bot tui' 启动图形界面以获得更好的交互体验")
    
    # 启动 AI 循环（由 Guardian 统一管理）
    try:
        await guardian.run_ai_loop()
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("接收到停止信号")
    finally:
        logger.info("Dev-Bot 停止")


def main():
    """入口点函数（命令行模式）"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()