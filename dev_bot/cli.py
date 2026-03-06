#!/usr/bin/env python3
"""
Dev-Bot 统一 CLI 入口
整合原有 dev-bot 功能和 SDD CLI 功能
"""

import argparse
import asyncio
import sys
from pathlib import Path


def main():
    """统一 CLI 主入口"""
    parser = argparse.ArgumentParser(
        prog='dev-bot',
        description='Dev-Bot - AI 驱动开发工具集',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用 'dev-bot <command> --help' 查看具体命令的帮助信息

可用模块:
  run      - 运行 AI 驱动开发循环（原有功能）
  sdd      - Spec Driven Development 工具集
  init     - 初始化 SDD 项目（快捷方式）

示例:
  dev-bot run                    # 运行 AI 开发循环
  dev-bot sdd init my-project    # 初始化 SDD 项目
  dev-bot sdd ai-spec feature    # 使用 AI 创建 spec
  dev-bot init my-project        # 快捷方式：初始化项目
  dev-bot auto-dev               # 自动化开发流程（通用）
  dev-bot auto-dev --mode analyze  # 仅分析项目
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Dev-Bot 3.0.0'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # run 命令 - 原有 dev-bot 功能
    run_parser = subparsers.add_parser(
        'run',
        help='运行 AI 驱动开发循环',
        description='运行 AI 驱动开发循环，自动调用 AI 工具完成开发任务'
    )
    run_parser.add_argument(
        '--config',
        '-c',
        default='config.json',
        help='配置文件路径（默认：config.json）'
    )
    run_parser.add_argument(
        '--no-tui',
        action='store_true',
        help='禁用 TUI 界面（使用命令行模式）'
    )

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 执行命令
    if args.command == 'run':
        # 调用原有的 dev-bot 功能
        if not args.no_tui:
            # TUI 模式（默认）- 使用进程协调器
            from dev_bot.process_coordinator import ProcessCoordinator

            async def run_tui_mode():
                # 使用进程协调器管理三个独立进程
                coordinator = ProcessCoordinator(Path.cwd())
                
                try:
                    await coordinator.start_all()
                except Exception as e:
                    print(f"协调器错误: {e}")
                finally:
                    await coordinator.stop_all()

            # 运行 TUI 模式
            try:
                asyncio.run(run_tui_mode())
            except KeyboardInterrupt:
                print("\n[!] TUI 模式已退出")
        else:
            # 命令行模式（使用 --no-tui 参数）
            from dev_bot.main import main as dev_bot_main
            sys.argv = ['dev-bot', '--config', args.config]
            dev_bot_main()


if __name__ == '__main__':
    main()
