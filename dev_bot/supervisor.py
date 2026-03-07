#!/usr/bin/env python3
"""Dev-Bot 监督器 - Guardian 的入口点"""

import sys
import asyncio
import logging

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


def main():
    """主函数 - Guardian 的轻量级入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Dev-Bot - AI 驱动的自主开发工具（所有模式都带 AI 守护）"
    )
    
    # 模式选择
    parser.add_argument(
        "mode",
        choices=["tui", "headless", "ai-loop"],
        nargs="?",
        default="headless",
        help="运行模式：tui（终端界面）、headless（无头模式，默认）或 ai-loop（AI 循环模式）"
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
    parser.add_argument(
        "--ai-loop-interval",
        type=int,
        default=1,
        help="AI 循环间隔秒数 (默认: 1)"
    )
    
    args = parser.parse_args()
    
    # 导入 Guardian（所有职责都由 Guardian 负责）
    try:
        from dev_bot.guardian import Guardian
        
        # 创建 Guardian 实例
        guardian = Guardian(
            max_restarts=args.max_restarts,
            restart_delay=args.restart_delay,
            ai_loop_interval=args.ai_loop_interval
        )
        
        # 根据模式启动
        if args.mode == "tui":
            command = ["python", "-m", "dev_bot.tui"]
            logger.info("启动 TUI 模式")
            # 运行 Guardian（所有逻辑都在这里）
            guardian.run_process(command)
        elif args.mode == "headless":
            command = ["python", "-m", "dev_bot.__main__"]
            logger.info("启动无头模式")
            # 运行 Guardian（所有逻辑都在这里）
            guardian.run_process(command)
        elif args.mode == "ai-loop":
            logger.info("启动 AI 循环模式")
            # 运行 AI 循环（由 Guardian 统一管理）
            asyncio.run(guardian.run_ai_loop())
        
    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n已停止")
        sys.exit(0)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()