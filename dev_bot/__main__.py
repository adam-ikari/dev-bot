#!/usr/bin/env python3
"""Dev-Bot 主入口 - 自动启动 AI 循环"""

import asyncio
import logging
import os
import sys
import signal as signal_module

from dev_bot.ai_runner import AIRunner

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


def setup_signal_handlers(runner):
    """设置信号处理器"""
    def signal_handler(signum, frame):
        logger.info(f"接收到信号 {signum}，正在停止...")
        runner.stop()
        sys.exit(0)
    
    signal_module.signal(signal_module.SIGTERM, signal_handler)
    signal_module.signal(signal_module.SIGINT, signal_handler)


async def main_async():
    """主异步函数"""
    runner = AIRunner()
    setup_signal_handlers(runner)
    
    logger.info("Dev-Bot 启动（命令行模式）")
    logger.info("提示: 使用 'dev-bot-tui' 启动图形界面以获得更好的交互体验")
    
    # 启动 AI 循环
    try:
        await runner.run()
        
        # 检查是否需要重启
        if runner.restart_pending:
            logger.info("🔄 正在重启以加载新代码...")
            with open(".restart-flag", "w") as f:
                f.write("restart")
            sys.exit(0)
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("接收到停止信号")
    finally:
        logger.info("Dev-Bot 停止")


def main():
    """入口点函数"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
