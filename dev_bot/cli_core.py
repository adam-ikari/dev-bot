#!/usr/bin/env python3

"""
Dev-Bot 核心 CLI - 精简的 AI 驱动开发系统

设计哲学：少即是多（Less is More）
- 专注核心功能
- 去除冗余复杂性
- 让 AI 做决策
"""

import argparse
from pathlib import Path

from dev_bot.core import create_bot


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        prog='dev-bot',
        description='Dev-Bot - AI 驱动的 Spec 开发系统'
    )

    parser.add_argument(
        'command',
        choices=['run', 'specs', 'help'],
        help='命令'
    )

    parser.add_argument(
        '--project-path', '-p',
        type=str,
        help='项目路径'
    )

    parser.add_argument(
        '--spec',
        type=str,
        help='Spec 文件'
    )

    parser.add_argument(
        '--ai-command',
        type=str,
        default='iflow',
        help='AI 命令'
    )

    parser.add_argument(
        '--tui',
        action='store_true',
        help='启用 TUI 界面（终端用户界面）'
    )

    args = parser.parse_args()

    if args.command == 'help':
        parser.print_help()
        return

    if args.command == 'specs':
        # 列出 Spec
        project_root = Path(args.project_path) if args.project_path else Path.cwd()
        specs_dir = project_root / "specs"

        if specs_dir.exists():
            print(f"Spec 文件 ({specs_dir}):")
            for spec_file in specs_dir.glob("*.json"):
                print(f"  - {spec_file.name}")
        else:
            print("未找到 specs 目录")
        return

    if args.command == 'run':
        # 运行 Dev-Bot
        project_root = Path(args.project_path) if args.project_path else Path.cwd()

        if args.tui:
            # TUI 模式
            from dev_bot.tui import DevBotTUI, TUILogger
            from dev_bot.core import create_bot
            import asyncio

            async def run_tui_mode():
                app = DevBotTUI()
                logger = TUILogger(app)
                
                logger.info("=" * 60)
                logger.info("Dev-Bot TUI 模式")
                logger.info("=" * 60)
                logger.info(f"项目路径: {project_root}")
                logger.info(f"Spec 文件: {args.spec or '自动检测'}")
                logger.info(f"AI 命令: {args.ai_command}")
                logger.info("=" * 60)
                
                # 创建 bot
                bot = create_bot(project_root)
                
                # 设置用户输入回调
                def handle_user_input(text: str):
                    bot.repl.add_input(text)
                
                app.set_user_input_callback(handle_user_input)
                
                # 运行
                async def run_bot_with_tui():
                    try:
                        # 使用 TUI 日志记录器
                        await asyncio.sleep(0.1)  # 让 TUI 启动
                        
                        logger.success("Dev-Bot 已启动")
                        logger.info("开始在 REPL 输入框中输入指令...")
                        
                        # 简化版运行逻辑
                        while True:
                            await asyncio.sleep(1)
                            
                            # 检查用户输入
                            if bot.repl.has_inputs():
                                inputs = bot.repl.get_inputs()
                                bot.repl.clear_inputs()
                                logger.info(f"收到 {len(inputs)} 条用户输入")
                            
                    except KeyboardInterrupt:
                        logger.warning("用户中断")
                    except Exception as e:
                        logger.error(f"运行错误: {e}")
                
                try:
                    async with app.run_task():
                        await run_bot_with_tui()
                except Exception as e:
                    logger.error(f"TUI 错误: {e}")
            
            # 运行 TUI 模式
            try:
                asyncio.run(run_tui_mode())
            except KeyboardInterrupt:
                print("\n[!] TUI 模式已退出")
        else:
            # 命令行模式
            print("="*60)
            print("Dev-Bot 核心 - AI 驱动的 Spec 开发系统")
            print("="*60)
            print()
            print("设计哲学: 少即是多")
            print()
            print("核心功能:")
            print("  1. Spec 驱动开发")
            print("  2. AI 循环")
            print("  3. REPL 模式")
            print("  4. 自动修复")
            print("  5. 自动重启")
            print()
            print(f"项目路径: {project_root}")
            print(f"Spec 文件: {args.spec or '自动检测'}")
            print(f"AI 命令: {args.ai_command}")
            print()
            print("提示: 使用 Ctrl+C 停止")
            print("="*60)
            print()

            # 创建并运行 bot
            bot = create_bot(project_root)

            try:
                bot.run(spec_file=args.spec)
            except KeyboardInterrupt:
                print("\n[!] 用户中断")
            except Exception as e:
                print(f"\n[!] 错误: {e}")
            finally:
                bot.stop()


if __name__ == '__main__':
    main()
