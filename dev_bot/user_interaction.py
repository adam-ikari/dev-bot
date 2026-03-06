#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户交互层

提供用户与 AI 守护系统交互的接口：
- 接收用户指令
- 转发指令到 AI 守护
- 显示系统状态
- 返回执行结果
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.ai_loop_control import AILoopController, AILoopCommand, AILoopState
from dev_bot.guardian import AIGuardian


class UserCommand(Enum):
    """用户命令枚举"""
    # AI 循环控制
    START_AI = "start_ai"
    STOP_AI = "stop_ai"
    PAUSE_AI = "pause_ai"
    RESUME_AI = "resume_ai"
    RESTART_AI = "restart_ai"
    
    # 状态查询
    STATUS = "status"
    AI_STATUS = "ai_status"
    GUARDIAN_STATUS = "guardian_status"
    LOGS = "logs"
    
    # 消息发送
    SEND = "send"
    
    # 帮助
    HELP = "help"
    EXIT = "exit"
    QUIT = "quit"


class UserInteractionLayer:
    """用户交互层
    
    提供用户与系统交互的接口
    """
    
    def __init__(self, project_root: Path, config_file: str = "config.json"):
        self.project_root = project_root
        self.config_file = config_file
        
        # 创建控制器
        self.ai_controller = AILoopController(project_root, config_file)
        self.ai_guardian = AIGuardian(check_interval=30)
        
        # 命令历史
        self.command_history: List[str] = []
        self.max_history = 100
        
        # 运行状态
        self.is_running = False
        
        print(f"[用户交互层] 初始化完成")
    
    async def start(self):
        """启动用户交互层"""
        print(f"[用户交互层] 启动中...")
        self.is_running = True
        
        # 启动 AI 守护
        await self.ai_guardian.start()
        
        # 注册 AI 循环进程
        self.ai_guardian.register_process(
            "ai_loop",
            None,
            self.ai_controller.startup_command,
            max_restarts=10
        )
        
        print(f"[用户交互层] 已启动")
        print(f"[用户交互层] 输入 'help' 查看可用命令")
    
    async def stop(self):
        """停止用户交互层"""
        print(f"[用户交互层] 停止中...")
        self.is_running = False
        
        # 停止 AI 守护
        await self.ai_guardian.stop()
        
        # 停止 AI 循环
        await self.ai_controller.stop()
        
        print(f"[用户交互层] 已停止")
    
    async def execute_command(self, command_str: str) -> str:
        """执行用户命令"""
        # 记录命令历史
        self.command_history.append(command_str)
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[-self.max_history:]
        
        # 解析命令
        parts = command_str.strip().split()
        if not parts:
            return "错误: 命令为空"
        
        cmd_str = parts[0].lower()
        args = parts[1:]
        
        # 匹配命令
        try:
            if cmd_str == UserCommand.START_AI.value:
                return await self._cmd_start_ai()
            elif cmd_str == UserCommand.STOP_AI.value:
                return await self._cmd_stop_ai()
            elif cmd_str == UserCommand.PAUSE_AI.value:
                return await self._cmd_pause_ai()
            elif cmd_str == UserCommand.RESUME_AI.value:
                return await self._cmd_resume_ai()
            elif cmd_str == UserCommand.RESTART_AI.value:
                return await self._cmd_restart_ai()
            elif cmd_str == UserCommand.STATUS.value:
                return await self._cmd_status()
            elif cmd_str == UserCommand.AI_STATUS.value:
                return await self._cmd_ai_status()
            elif cmd_str == UserCommand.GUARDIAN_STATUS.value:
                return await self._cmd_guardian_status()
            elif cmd_str == UserCommand.LOGS.value:
                lines = int(args[0]) if args and args[0].isdigit() else 50
                return await self._cmd_logs(lines)
            elif cmd_str == UserCommand.SEND.value:
                if len(args) < 1:
                    return "错误: 缺少消息内容"
                message = " ".join(args)
                return await self._cmd_send(message)
            elif cmd_str == UserCommand.HELP.value:
                return self._cmd_help()
            elif cmd_str in [UserCommand.EXIT.value, UserCommand.QUIT.value]:
                return self._cmd_exit()
            else:
                return f"错误: 未知命令 '{cmd_str}'，输入 'help' 查看可用命令"
                
        except Exception as e:
            return f"错误: 执行命令时出错: {e}"
    
    async def _cmd_start_ai(self) -> str:
        """启动 AI 循环"""
        success = await self.ai_controller.start()
        if success:
            return "✓ AI 循环已启动"
        else:
            return "✗ AI 循环启动失败"
    
    async def _cmd_stop_ai(self) -> str:
        """停止 AI 循环"""
        success = await self.ai_controller.stop()
        if success:
            return "✓ AI 循环已停止"
        else:
            return "✗ AI 循环停止失败"
    
    async def _cmd_pause_ai(self) -> str:
        """暂停 AI 循环"""
        success = await self.ai_controller.pause()
        if success:
            return "✓ AI 循环已暂停"
        else:
            return "✗ AI 循环暂停失败"
    
    async def _cmd_resume_ai(self) -> str:
        """恢复 AI 循环"""
        success = await self.ai_controller.resume()
        if success:
            return "✓ AI 循环已恢复"
        else:
            return "✗ AI 循环恢复失败"
    
    async def _cmd_restart_ai(self) -> str:
        """重启 AI 循环"""
        success = await self.ai_controller.restart()
        if success:
            return "✓ AI 循环已重启"
        else:
            return "✗ AI 循环重启失败"
    
    async def _cmd_status(self) -> str:
        """获取系统状态"""
        ai_status = await self.ai_controller.get_status()
        guardian_status = self.ai_guardian.get_status()
        
        result = [
            "=== 系统状态 ===",
            f"AI 循环: {ai_status.get('state', 'unknown')} (PID: {ai_status.get('pid', 'N/A')})",
            f"AI 守护: {'运行中' if guardian_status['core_guardian']['is_running'] else '已停止'}",
            f"恢复次数: {guardian_status['core_guardian']['recovery_count']}",
        ]
        
        return "\n".join(result)
    
    async def _cmd_ai_status(self) -> str:
        """获取 AI 循环状态"""
        status = await self.ai_controller.get_status()
        
        result = [
            "=== AI 循环状态 ===",
            f"状态: {status.get('state', 'unknown')}",
            f"PID: {status.get('pid', 'N/A')}",
        ]
        
        return "\n".join(result)
    
    async def _cmd_guardian_status(self) -> str:
        """获取 AI 守护状态"""
        status = self.ai_guardian.get_status()
        
        result = [
            "=== AI 守护状态 ===",
            f"运行状态: {'运行中' if status['core_guardian']['is_running'] else '已停止'}",
            f"恢复次数: {status['core_guardian']['recovery_count']}",
            f"检查间隔: {status['core_guardian']['check_interval']}秒",
            f"监控进程数: {len(status['core_guardian']['monitored_processes'])}",
        ]
        
        return "\n".join(result)
    
    async def _cmd_logs(self, lines: int = 50) -> str:
        """获取 AI 循环日志"""
        logs = await self.ai_controller.get_logs(lines)
        
        if not logs:
            return "没有可用的日志"
        
        result = [f"=== 最近 {len(logs)} 条日志 ==="]
        result.extend(logs[-lines:])
        
        return "\n".join(result)
    
    async def _cmd_send(self, message: str) -> str:
        """发送消息到 AI 循环"""
        success = await self.ai_controller.send_message(message)
        if success:
            return f"✓ 消息已发送: {message[:50]}..."
        else:
            return "✗ 消息发送失败"
    
    def _cmd_help(self) -> str:
        """显示帮助信息"""
        help_text = """
=== 可用命令 ===

AI 循环控制:
  start_ai      - 启动 AI 循环
  stop_ai       - 停止 AI 循环
  pause_ai      - 暂停 AI 循环
  resume_ai     - 恢复 AI 循环
  restart_ai    - 重启 AI 循环

状态查询:
  status        - 查看系统状态
  ai_status     - 查看 AI 循环状态
  guardian_status - 查看 AI 守护状态
  logs [N]      - 查看最近 N 条日志（默认 50）

消息发送:
  send <msg>    - 发送消息到 AI 循环

其他:
  help          - 显示此帮助信息
  exit / quit   - 退出系统
"""
        return help_text
    
    def _cmd_exit(self) -> str:
        """退出系统"""
        return "exit"
    
    def get_command_history(self) -> List[str]:
        """获取命令历史"""
        return self.command_history.copy()
    
    def clear_history(self):
        """清空命令历史"""
        self.command_history.clear()


async def interactive_mode(user_layer: UserInteractionLayer):
    """交互模式"""
    print("\n" + "=" * 60)
    print("Dev-Bot 用户交互层")
    print("=" * 60)
    print("输入 'help' 查看可用命令")
    print("输入 'exit' 或 'quit' 退出")
    print("=" * 60 + "\n")
    
    try:
        while user_layer.is_running:
            try:
                # 读取用户输入
                cmd = input(f"[dev-bot] > ").strip()
                
                if not cmd:
                    continue
                
                # 执行命令
                result = await user_layer.execute_command(cmd)
                
                # 显示结果
                print(result)
                
                # 检查是否退出
                if result == "exit":
                    await user_layer.stop()
                    break
                    
            except EOFError:
                print("\n检测到 EOF，退出...")
                await user_layer.stop()
                break
            except KeyboardInterrupt:
                print("\n按 Ctrl+C 退出...")
                await user_layer.stop()
                break
                
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    project_root = Path.cwd()
    
    # 创建用户交互层
    user_layer = UserInteractionLayer(project_root)
    
    # 启动
    await user_layer.start()
    
    # 进入交互模式
    await interactive_mode(user_layer)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已停止")
