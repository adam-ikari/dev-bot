#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dev-Bot - 极简 AI 驱动开发代理

类似 OpenOAI 的极简实现：
- 只负责调用 iflow
- 不实现任何具体功能
- 支持多端交互（TUI/Web/API）
- 支持自我迭代
- 支持AI对话
"""

import argparse
import asyncio
import sys
from pathlib import Path

from dev_bot.core import get_core
from dev_bot.interaction import get_interaction_manager, InteractionMode
from dev_bot.self_iteration_simple import SimpleSelfIteration


def main_parser():
    """创建主解析器"""
    parser = argparse.ArgumentParser(
        description="Dev-Bot - 极简 AI 驱动开发代理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 交互模式（默认启动 TUI）
  dev-bot                          # 启动 TUI 模式（默认）
  dev-bot ui                       # 启动 TUI 模式
  dev-bot ui --mode web            # 启动 Web 模式
  dev-bot ui --mode api            # 启动 API 模式
  
  # 快速执行
  dev-bot run --plan "分析"        # 规划模式
  dev-bot run -y "执行"            # 执行模式
  dev-bot run --thinking "思考"    # 思考模式
  dev-bot run --headless "任务"    # 无头模式（自动化）
  
  # 迭代系统
  dev-bot iterate                  # 运行一次自我迭代
  dev-bot iterate --continuous     # 启动连续自我迭代
  dev-bot iterate --project /path/to/project  # 迭代其他项目
  
  # 对话系统
  dev-bot dialogue create "主题"    # 创建对话
  dev-bot dialogue list            # 列出所有对话

默认行为：
  - 不带参数运行时，默认启动 TUI 模式
  - TUI 模式提供交互式命令行界面
  - 支持提交问题、查看队列、管理对话等功能
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # UI 命令
    ui_parser = subparsers.add_parser("ui", help="启动用户界面")
    ui_parser.add_argument(
        "--mode",
        choices=["tui", "web", "api"],
        default="tui",
        help="交互模式（默认: tui）"
    )
    ui_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Web/API 监听地址（默认: 127.0.0.1）"
    )
    ui_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Web/API 监听端口（默认: 8080）"
    )
    
    # Run 命令
    run_parser = subparsers.add_parser("run", help="快速执行")
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
        "--headless",
        action="store_true",
        help="无头模式（全自动运行，无交互）"
    )
    run_parser.add_argument(
        "--api-host",
        default="127.0.0.1",
        help="API 主机地址（默认: 127.0.0.1）"
    )
    run_parser.add_argument(
        "--api-port",
        type=int,
        default=8080,
        help="API 端口（默认: 8080）"
    )
    run_parser.add_argument(
        "prompt",
        help="提示词"
    )
    
    # Iterate 命令
    iterate_parser = subparsers.add_parser("iterate", help="迭代系统")
    iterate_parser.add_argument(
        "--continuous",
        action="store_true",
        help="连续迭代模式"
    )
    iterate_parser.add_argument(
        "--interval",
        type=int,
        default=1800,
        help="迭代间隔（秒，默认: 1800）"
    )
    iterate_parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="项目路径（默认: 当前目录）"
    )
    iterate_parser.add_argument(
        "--once",
        action="store_true",
        help="只运行一次迭代"
    )
    
    # Dialogue 命令
    dialogue_parser = subparsers.add_parser("dialogue", help="对话系统")
    dialogue_subparsers = dialogue_parser.add_subparsers(dest="dialogue_action", help="对话操作")
    
    # Dialogue create
    dialogue_create_parser = dialogue_subparsers.add_parser("create", help="创建对话")
    dialogue_create_parser.add_argument("topic", help="对话主题")
    dialogue_create_parser.add_argument("--participants", nargs="+", help="参与者")
    
    # Dialogue list
    dialogue_subparsers.add_parser("list", help="列出所有对话")
    
    # Dialogue info
    dialogue_info_parser = dialogue_subparsers.add_parser("info", help="查看对话信息")
    dialogue_info_parser.add_argument("dialogue_id", help="对话 ID")
    
    # Dialogue run
    dialogue_run_parser = dialogue_subparsers.add_parser("run", help="运行对话")
    dialogue_run_parser.add_argument("dialogue_id", help="对话 ID")
    dialogue_run_parser.add_argument("--duration", type=int, default=300, help="最大持续时间（秒）")
    
    return parser


async def handle_ui(args):
    """处理 UI 命令"""
    manager = get_interaction_manager()
    
    print("Dev-Bot - 极简 AI 驱动开发代理")
    print("类似 OpenOAI：只负责调用 iflow，不实现任何具体功能")
    print(f"模式: {args.mode}")
    print()
    
    # 启动 AI 守护进程（如果是 TUI 模式）
    guardian_process = None
    process_manager = None
    if args.mode == "tui":
        try:
            from dev_bot.process_manager import ProcessManager
            from pathlib import Path
            
            process_manager = ProcessManager()
            guardian_script = Path.cwd() / "dev_bot" / "guardian_process.py"
            
            if guardian_script.exists():
                print(f"[系统] 启动 AI 守护进程...")
                guardian_process = await process_manager.create_process(
                    process_id="ai_guardian",
                    script_path=guardian_script,
                    args=[],
                    cwd=Path.cwd(),
                    use_new_session=True  # AI 守护在新的会话中运行
                )
                
                if guardian_process:
                    print(f"[系统] ✓ AI 守护已启动 (PID: {guardian_process.pid})")
                    
                    # 等待 AI 守护初始化
                    await asyncio.sleep(2)
                else:
                    print(f"[系统] ✗ AI 守护启动失败，继续运行但后台功能不可用")
            else:
                print(f"[系统] 警告: AI 守护脚本不存在: {guardian_script}")
        except Exception as e:
            print(f"[系统] 警告: 启动 AI 守护失败: {e}")
            print(f"[系统] 继续运行，但后台 AI 实例可能不可用")
    
    try:
        if args.mode == "tui":
            await manager.start_tui()
        elif args.mode == "web":
            await manager.start_web(args.host, args.port)
        elif args.mode == "api":
            await manager.start_api(args.host, args.port)
    except KeyboardInterrupt:
        print("\nDev-Bot 已停止")
    finally:
        # 停止 AI 守护进程
        if guardian_process and process_manager:
            try:
                await process_manager.terminate_process("ai_guardian")
                print(f"[系统] AI 守护已停止")
            except Exception as e:
                print(f"[系统] 警告: 停止 AI 守护时出错: {e}")
        
        await manager.stop()


async def handle_run(args):
    """处理 Run 命令"""
    core = get_core()
    
    # 选择模式
    mode = "normal"
    if args.plan:
        mode = "plan"
    elif args.y:
        mode = "execute"
    elif args.thinking:
        mode = "thinking"
    
    # 执行任务
    if mode == "plan":
        result = await core.plan(args.prompt)
    elif mode == "execute":
        result = await core.execute(args.prompt)
    elif mode == "thinking":
        result = await core.think(args.prompt)
    else:
        result = await core.call_iflow(args.prompt)
    
    # 输出结果
    if args.headless:
        # 无头模式：输出 JSON 格式
        import json
        output = {
            "success": result["success"],
            "mode": mode,
            "duration": result.get("duration", 0),
            "output": result.get("output", ""),
            "error": result.get("error", "")
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        # 交互模式：输出人类可读格式
        if result["success"]:
            print(f"✓ 成功（耗时: {result.get('duration', 0):.2f}秒）")
            print(result.get("output", ""))
        else:
            print(f"✗ 失败: {result.get('error', 'Unknown error')}")
            if result.get("output"):
                print(result["output"])


async def handle_iterate(args):
    """处理 Iterate 命令"""
    iteration = SimpleSelfIteration(args.project)
    
    if args.once or not args.continuous:
        # 运行一次迭代
        print(f"运行一次迭代: {args.project}")
        result = await iteration.run_iteration()
        
        print(f"\n迭代 ID: {result['iteration_id']}")
        print(f"决策: {result['decision']['action']}")
        print(f"执行成功: {result['execution']['success']}")
        print(f"改进成功: {result['verification']['success']}")
    else:
        # 连续迭代模式
        print(f"启动连续迭代模式")
        print(f"项目: {args.project}")
        print(f"间隔: {args.interval} 秒")
        print("按 Ctrl+C 停止")
        print()
        
        try:
            await iteration.start_continuous_iteration(interval=args.interval)
        except KeyboardInterrupt:
            print("\n迭代已停止")
        finally:
            iteration.stop()


async def handle_dialogue(args):
    """处理 Dialogue 命令"""
    from dev_bot.dialogue_integrator import DialogueIntegrator
    from dev_bot.ai_dialogue import DialogueMode
    
    integrator = DialogueIntegrator()
    integrator._initialize()
    
    if args.dialogue_action == "create":
        # 创建对话
        participants = args.participants or ["analyzer", "developer", "tester"]
        
        dialogue_id = integrator.dialogue_manager.create_dialogue(
            participants=participants,
            topic=args.topic,
            mode=DialogueMode.GROUP
        )
        
        print(f"✓ 对话已创建: {dialogue_id}")
        print(f"  主题: {args.topic}")
        print(f"  参与者: {', '.join(participants)}")
    
    elif args.dialogue_action == "list":
        # 列出所有对话
        dialogues = await integrator.list_dialogues()
        
        print(f"共有 {len(dialogues)} 个对话:\n")
        for d in dialogues:
            print(f"  ID: {d.dialogue_id}")
            print(f"  主题: {d.topic}")
            print(f"  状态: {'活跃' if d.is_active else '结束'}")
            print(f"  消息数: {len(d.messages)}")
            print()
    
    elif args.dialogue_action == "info":
        # 查看对话信息
        dialogue = await integrator.get_dialogue(args.dialogue_id)
        
        if not dialogue:
            print(f"✗ 对话不存在: {args.dialogue_id}")
            return
        
        print(f"对话 ID: {dialogue.dialogue_id}")
        print(f"主题: {dialogue.topic}")
        print(f"状态: {'活跃' if dialogue.is_active else '结束'}")
        print(f"参与者: {', '.join(dialogue.participants)}")
        print(f"消息数: {len(dialogue.messages)}")
        print()
        
        if dialogue.messages:
            print("最近消息:")
            for msg in list(dialogue.messages)[-5:]:
                speaker = dialogue.participants.get(msg.sender_id, msg.sender_id)
                print(f"  [{speaker}]: {msg.content[:100]}")
    
    elif args.dialogue_action == "run":
        # 运行对话
        print(f"运行对话: {args.dialogue_id}")
        print(f"最大持续时间: {args.duration} 秒")
        print()
        
        success = await integrator.run_dialogue(args.dialogue_id, max_duration=args.duration)
        
        if success:
            print("✓ 对话完成")
        else:
            print("✗ 对话失败")


async def main():
    """主函数"""
    parser = main_parser()
    args = parser.parse_args()
    
    # 如果没有子命令，默认运行 UI
    if args.command is None:
        args.command = "ui"
        args.mode = "tui"
        args.host = "127.0.0.1"
        args.port = 8080
    
    # 根据命令调用对应的处理函数
    if args.command == "ui":
        await handle_ui(args)
    elif args.command == "run":
        await handle_run(args)
    elif args.command == "iterate":
        await handle_iterate(args)
    elif args.command == "dialogue":
        await handle_dialogue(args)
    else:
        parser.print_help()


def cli():
    """CLI 入口函数（同步包装）"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDev-Bot 已停止")
        sys.exit(0)


if __name__ == '__main__':
    cli()