#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dev-Bot - 极简 AI 驱动开发代理

类似 OpenOAI 的极简实现：
- 只负责调用 iflow
- 不实现任何具体功能
- 支持多端交互（TUI/Web/API）
"""

import argparse
import asyncio
import sys
from pathlib import Path

from dev_bot.core import get_core
from dev_bot.interaction import get_interaction_manager, InteractionMode


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Dev-Bot - 极简 AI 驱动开发代理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  dev-bot                  # 启动 TUI 模式
  dev-bot --mode web       # 启动 Web 模式
  dev-bot --mode api       # 启动 API 模式
  dev-bot run --plan "分析"    # 规划模式
  dev-bot run -y "执行"        # 执行模式
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="运行命令")
    
    run_parser.add_argument(
        "--mode",
        choices=["tui", "web", "api"],
        default="tui",
        help="交互模式（默认: tui）"
    )
    
    run_parser.add_argument(
        "--plan",
        action="store_true",
        help="规划模式"
    )
    
    run_parser.add_argument(
        "-y",
        action="store_true",
        help="执行模式"
    )
    
    run_parser.add_argument(
        "--thinking",
        action="store_true",
        help="思考模式"
    )
    
    run_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Web/API 监听地址（默认: 127.0.0.1）"
    )
    
    run_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Web/API 监听端口（默认: 8080）"
    )
    
    run_parser.add_argument(
        "prompt",
        nargs="*",
        help="提示词"
    )
    
    args = parser.parse_args()
    
    # 如果有提示词参数，直接执行
    if args.command == "run" and args.prompt:
        prompt = " ".join(args.prompt)
        core = get_core()
        
        if args.plan:
            result = await core.plan(prompt)
        elif args.y:
            result = await core.execute(prompt)
        elif args.thinking:
            result = await core.think(prompt)
        else:
            result = await core.call_iflow(prompt)
        
        if result["success"]:
            print(f"✓ 成功（耗时: {result['duration']:.2f}秒）")
            print(result["output"])
        else:
            print(f"✗ 失败: {result['error']}")
        
        return
    
    # 否则启动交互层
    if args.command:
        manager = get_interaction_manager()
        
        print("Dev-Bot - 极简 AI 驱动开发代理")
        print("类似 OpenOAI：只负责调用 iflow，不实现任何具体功能")
        print(f"模式: {args.mode}")
        print()
        
        try:
            if args.mode == "tui":
                manager.start_tui()
            elif args.mode == "web":
                await manager.start_web(args.host, args.port)
            elif args.mode == "api":
                await manager.start_api(args.host, args.port)
        except KeyboardInterrupt:
            print("\nDev-Bot 已停止")
        finally:
            await manager.stop()
    else:
        parser.print_help()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDev-Bot 已停止")
        sys.exit(0)
