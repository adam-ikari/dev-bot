#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SDD CLI - Spec Driven Development 命令行工具
"""

import argparse
import sys
from pathlib import Path

from dev_bot.cli.commands import InitCommand, NewSpecCommand, ValidateCommand, AISpecCommand


def main():
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        prog='sdd',
        description='Spec Driven Development - 基于 spec 的开发工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  sdd init my-project          # 初始化 SDD 项目
  sdd new-spec feature.json    # 创建新的 spec 文件
  sdd validate feature.json    # 验证 spec 文件
  sdd ai-spec user-auth --type feature --desc "用户认证功能"  # 使用 AI 创建 spec
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init 命令
    init_parser = subparsers.add_parser(
        'init',
        help='初始化 SDD 项目'
    )
    init_parser.add_argument(
        'project_name',
        help='项目名称'
    )
    init_parser.add_argument(
        '--template',
        choices=['minimal', 'standard', 'full'],
        default='standard',
        help='项目模板类型'
    )
    
    # new-spec 命令
    spec_parser = subparsers.add_parser(
        'new-spec',
        help='创建新的 spec 文件'
    )
    spec_parser.add_argument(
        'spec_name',
        help='spec 文件名（不包含扩展名）'
    )
    spec_parser.add_argument(
        '--type',
        choices=['feature', 'api', 'component', 'service'],
        default='feature',
        help='spec 类型'
    )
    spec_parser.add_argument(
        '--output',
        help='输出目录（默认：specs/）'
    )
    
    # validate 命令
    validate_parser = subparsers.add_parser(
        'validate',
        help='验证 spec 文件'
    )
    validate_parser.add_argument(
        'spec_file',
        help='spec 文件路径'
    )
    
    # ai-spec 命令
    ai_parser = subparsers.add_parser(
        'ai-spec',
        help='使用 AI 创建 spec 文件'
    )
    ai_parser.add_argument(
        'spec_name',
        help='spec 文件名（不包含扩展名）'
    )
    ai_parser.add_argument(
        '--type',
        choices=['feature', 'api', 'component', 'service'],
        default='feature',
        help='spec 类型'
    )
    ai_parser.add_argument(
        '--desc',
        '--description',
        help='spec 描述，帮助 AI 更好地生成内容'
    )
    ai_parser.add_argument(
        '--ai-tool',
        help='AI 工具命令（默认：iflow）'
    )
    ai_parser.add_argument(
        '--output',
        help='输出目录（默认：specs/）'
    )
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 执行命令
    commands = {
        'init': InitCommand,
        'new-spec': NewSpecCommand,
        'validate': ValidateCommand,
        'ai-spec': AISpecCommand,
    }
    
    command_class = commands.get(args.command)
    if command_class:
        cmd = command_class(args)
        cmd.execute()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()