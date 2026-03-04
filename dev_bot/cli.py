#!/usr/bin/env python3

"""
Dev-Bot 统一 CLI 入口
整合原有 dev-bot 功能和 SDD CLI 功能
"""

import argparse
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
        version='Dev-Bot 2.0.0'
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

    # sdd 命令 - Spec Driven Development
    sdd_parser = subparsers.add_parser(
        'sdd',
        help='Spec Driven Development 工具',
        description='基于 spec 的开发工具集'
    )
    sdd_subparsers = sdd_parser.add_subparsers(dest='sdd_command', help='SDD 子命令')

    # sdd init
    init_parser = sdd_subparsers.add_parser('init', help='初始化 SDD 项目')
    init_parser.add_argument('project_name', help='项目名称')
    init_parser.add_argument(
        '--template',
        choices=['minimal', 'standard', 'full'],
        default='standard',
        help='项目模板类型'
    )

    # sdd new-spec
    new_spec_parser = sdd_subparsers.add_parser('new-spec', help='创建新的 spec 文件')
    new_spec_parser.add_argument('spec_name', help='spec 文件名')
    new_spec_parser.add_argument(
        '--type',
        choices=['feature', 'api', 'component', 'service'],
        default='feature',
        help='spec 类型'
    )
    new_spec_parser.add_argument('--output', help='输出目录')

    # sdd ai-spec
    ai_spec_parser = sdd_subparsers.add_parser('ai-spec', help='使用 AI 创建 spec')
    ai_spec_parser.add_argument('spec_name', help='spec 文件名')
    ai_spec_parser.add_argument(
        '--type',
        choices=['feature', 'api', 'component', 'service'],
        default='feature',
        help='spec 类型'
    )
    ai_spec_parser.add_argument('--desc', '--description', help='spec 描述')
    ai_spec_parser.add_argument('--ai-tool', help='AI 工具命令')
    ai_spec_parser.add_argument('--output', help='输出目录')

    # sdd validate
    validate_parser = sdd_subparsers.add_parser('validate', help='验证 spec 文件')
    validate_parser.add_argument('spec_file', help='spec 文件路径')

    # sdd enhance
    enhance_parser = sdd_subparsers.add_parser('enhance', help='使用 AI 增强 spec 文件')
    enhance_parser.add_argument('spec_file', help='spec 文件路径')
    enhance_parser.add_argument(
        '--aspect',
        choices=['requirements', 'user_stories', 'acceptance_criteria', 'api', 'components', 'tests', 'examples', 'security', 'performance', 'all'],
        default='all',
        help='增强方面'
    )
    enhance_parser.add_argument('--ai-tool', help='AI 工具命令')

    # sdd extract-spec
    extract_parser = sdd_subparsers.add_parser('extract-spec', help='从已有工程提取 spec')
    extract_parser.add_argument('project_path', help='工程路径（默认为当前目录）', nargs='?', default='.')
    extract_parser.add_argument(
        '--type',
        choices=['feature', 'api', 'component', 'service'],
        default='feature',
        help='spec 类型'
    )
    extract_parser.add_argument('--output', help='输出目录（默认：specs/）')
    extract_parser.add_argument('--spec-name', help='spec 文件名（默认：工程名称）')
    extract_parser.add_argument('--ai-tool', help='AI 工具命令')
    extract_parser.add_argument('--no-ai', action='store_true', help='不使用 AI，仅基于代码分析')

    # init 命令 - 快捷方式
    init_short_parser = subparsers.add_parser(
        'init',
        help='初始化 SDD 项目（快捷方式）',
        add_help=False
    )
    init_short_parser.add_argument('project_name', help='项目名称')
    init_short_parser.add_argument(
        '--template',
        choices=['minimal', 'standard', 'full'],
        default='standard',
        help='项目模板类型'
    )

    # auto-dev 命令 - 自动化开发流程
    auto_dev_parser = subparsers.add_parser(
        'auto-dev',
        help='自动化工程开发流程',
        description='自动分析项目、生成 spec、验证、增强并提供建议'
    )
    auto_dev_parser.add_argument(
        '--mode', '-m',
        choices=['auto', 'analyze', 'generate', 'validate', 'enhance', 'suggest'],
        default='auto',
        help='运行模式'
    )
    auto_dev_parser.add_argument('--ai-tool', '-t', help='AI 工具命令')
    auto_dev_parser.add_argument('--project-path', '-p', help='项目路径（默认：当前目录）')
    auto_dev_parser.add_argument('--no-auto-fix', action='store_true', help='禁用自动修复')
    auto_dev_parser.add_argument('--no-auto-restart', action='store_true', help='禁用自动重启')
    auto_dev_parser.add_argument('--no-auto-git', action='store_true', help='禁用自动 Git 管理')

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 执行命令
    if args.command == 'run':
        # 调用原有的 dev-bot 功能
        if not args.no_tui:
            # TUI 模式（默认）
            import asyncio

            from dev_bot.core import create_bot
            from dev_bot.tui import DevBotTUI, TUILogger

            async def run_tui_mode():
                app = DevBotTUI()
                logger = TUILogger(app)

                project_root = Path(args.config).parent if args.config != 'config.json' else Path.cwd()

                logger.info("=" * 60)
                logger.info("Dev-Bot TUI 模式")
                logger.info("=" * 60)
                logger.info(f"项目路径: {project_root}")
                logger.info(f"配置文件: {args.config}")
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
            # 命令行模式（使用 --no-tui 参数）
            from dev_bot.main import main as dev_bot_main
            sys.argv = ['dev-bot', '--config', args.config]
            dev_bot_main()

    elif args.command == 'sdd':
        if not args.sdd_command:
            sdd_parser.print_help()
            sys.exit(0)

        from dev_bot.cli.commands import AISpecCommand, InitCommand, NewSpecCommand, ValidateCommand

        sdd_commands = {
            'init': InitCommand,
            'new-spec': NewSpecCommand,
            'ai-spec': AISpecCommand,
            'validate': ValidateCommand,
            'enhance': 'enhance',
            'extract-spec': 'extract_spec',
        }

        cmd_class = sdd_commands.get(args.sdd_command)
        if cmd_class:
            if cmd_class == 'enhance':
                from dev_bot.cli.enhance import EnhanceSpecCommand
                cmd = EnhanceSpecCommand(args)
            elif cmd_class == 'extract_spec':
                from dev_bot.cli.extract import ExtractSpecCommand
                cmd = ExtractSpecCommand(args)
            else:
                cmd = cmd_class(args)
            cmd.execute()

    elif args.command == 'init':
        # 快捷方式：sdd init
        from dev_bot.cli.commands import InitCommand
        cmd = InitCommand(args)
        cmd.execute()

    elif args.command == 'auto-dev':
        # 自动化开发流程
        from dev_bot.auto_project_dev import AutoProjectDevelopment
        project_path = Path(args.project_path) if args.project_path else Path.cwd()
        auto_dev = AutoProjectDevelopment(
            project_path,
            args.ai_tool or 'iflow',
            args.mode,
            auto_fix=not args.no_auto_fix,
            auto_restart=not args.no_auto_restart,
            auto_git=not args.no_auto_git
        )
        auto_dev.run()


if __name__ == '__main__':
    main()
