#!/usr/bin/env python3
"""Dev-Bot 监督器 - Guardian 的入口点"""

import sys


def main():
    """主函数 - Guardian 的轻量级入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Dev-Bot - AI 驱动的自主开发工具（所有模式都带 AI 守护）"
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
    
    # 导入 Guardian（所有职责都由 Guardian 负责）
    try:
        from dev_bot.guardian import Guardian
        
        # 创建 Guardian 实例
        guardian = Guardian(
            max_restarts=args.max_restarts,
            restart_delay=args.restart_delay
        )
        
        # 根据模式启动
        if args.mode == "tui":
            command = ["python", "-m", "dev_bot.tui"]
        else:  # headless
            command = ["python", "-m", "dev_bot.__main__"]
        
        # 运行 Guardian（所有逻辑都在这里）
        guardian.run_process(command)
        
    except KeyboardInterrupt:
        print("\n已停止")
        sys.exit(0)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()