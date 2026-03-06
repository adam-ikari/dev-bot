#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 循环 - 指令调度版本

重新设计为纯粹的指令调度系统：
- 生成指令
- 调度执行
- 跟踪状态
- 不直接执行工作
"""

import asyncio
import json
import os
import signal
import sys
from pathlib import Path
from typing import Dict, Any, List

from dev_bot.ipc import IPCManager
from dev_bot.main import Config
from dev_bot.command_scheduler import (
    get_command_scheduler,
    Command,
    CommandType,
    CommandPriority
)


class AILoopScheduler:
    """AI 循环调度器（指令调度版本）
    
    纯粹的指令调度系统，不给 iflow 下具体的实现指令
    """
    
    def __init__(self, project_root: Path, config_file: str):
        self.project_root = project_root
        self.config_file = config_file
        self.config = Config(config_file)
        self.ipc = IPCManager(project_root)
        
        self.is_running = False
        self.is_paused = False
        self.session_num = 1
        
        # 指令调度系统
        self.command_scheduler = get_command_scheduler(
            project_root,
            self.config.get_ai_command()
        )
        
        # 记忆文件
        self.memory_file = project_root / ".dev-bot-memory" / "context.json"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 命令和响应文件
        self.command_file = project_root / ".ipc" / "ai_loop_command.json"
        self.response_file = project_root / ".ipc" / "ai_loop_response.json"
        
        print(f"[AI循环调度器] 初始化完成（PID: {os.getpid()}）")
        print(f"[AI循环调度器] 模式: 纯指令调度")
    
    async def run(self):
        """运行 AI 循环"""
        self.is_running = True
        
        print(f"[AI循环调度器] 启动 AI 循环进程")
        
        # 更新状态
        self._update_status({"status": "running", "session": 0})
        
        try:
            # 主循环
            while self.is_running:
                await self._schedule_session()
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"[AI循环调度器] AI 循环出错: {e}")
            self._update_status({"status": "error", "error": str(e)})
        finally:
            print(f"[AI循环调度器] AI 循环进程退出")
            self._update_status({"status": "stopped"})
    
    async def _schedule_session(self):
        """调度一次会话"""
        self._log("info", f">>> 指令调度 #{self.session_num} <<<")
        
        # 检查用户命令
        user_command = await self._check_user_command()
        if user_command:
            await self._process_user_command(user_command)
        else:
            # 自动生成指令
            await self._auto_generate_commands()
        
        # 更新状态
        self._update_status({
            "status": "running",
            "session": self.session_num,
            "last_activity": __import__('datetime').datetime.now().isoformat()
        })
        
        self.session_num += 1
    
    async def _auto_generate_commands(self):
        """自动生成指令"""
        self._log("info", "[自动生成] 分析项目状态，生成指令...")
        
        # 加载记忆
        memory = self._load_memory()
        
        # 生成分析指令
        analyze_command = self.command_scheduler.generate_command(
            CommandType.ANALYZE,
            {"session": self.session_num, "memory": memory}
        )
        
        if analyze_command:
            self._log("info", f"[自动生成] 生成指令: {analyze_command.id}")
            
            # 执行队列
            queue_status = self.command_scheduler.get_queue_status()
            self._log("info", f"[指令队列] 待执行: {queue_status['pending']} 个")
            
            # 执行指令
            await self.command_scheduler.execute_queue(max_concurrent=1)
            
            # 更新记忆
            memory['history'].append({
                "session": self.session_num,
                "phase": "command_scheduled",
                "timestamp": __import__('datetime').datetime.now().isoformat(),
                "content": f"调度了 {queue_status['pending']} 个指令"
            })
            self._save_memory(memory)
            
            self._log("success", f"指令调度 #{self.session_num} 完成")
        else:
            self._log("warning", f"指令调度 #{self.session_num} 跳过（无指令）")
    
    async def _process_user_command(self, user_command: Dict):
        """处理用户命令"""
        self._log("info", f"[用户命令] 处理用户指令: {user_command.get('command')}")
        
        command_type = user_command.get("type", "analyze")
        
        # 映射命令类型
        type_mapping = {
            "analyze": CommandType.ANALYZE,
            "develop": CommandType.DEVELOP,
            "debug": CommandType.DEBUG,
            "test": CommandType.TEST,
            "optimize": CommandType.OPTIMIZE,
            "refactor": CommandType.REFACTOR,
            "document": CommandType.DOCUMENT,
            "deploy": CommandType.DEPLOY
        }
        
        cmd_type = type_mapping.get(command_type, CommandType.ANALYZE)
        
        # 生成指令
        command = self.command_scheduler.generate_command(
            cmd_type,
            {
                "session": self.session_num,
                "user_command": user_command,
                "task": user_command.get("task", ""),
                "description": user_command.get("description", "")
            }
        )
        
        if command:
            # 执行指令
            await self.command_scheduler.execute_queue(max_concurrent=1)
            
            # 保存结果
            self._save_response({
                "success": True,
                "command_id": command.id,
                "message": f"用户命令已执行: {user_command.get('command')}"
            })
        else:
            self._save_response({
                "success": False,
                "error": f"无法生成指令: {command_type}"
            })
    
    async def _check_user_command(self) -> Optional[Dict]:
        """检查用户命令"""
        if not self.command_file.exists():
            return None
        
        try:
            with open(self.command_file, 'r', encoding='utf-8') as f:
                command_data = json.load(f)
            
            # 删除命令文件
            self.command_file.unlink()
            
            return command_data
            
        except Exception as e:
            self._log("error", f"读取用户命令失败: {e}")
            return None
    
    def _save_response(self, response: Dict):
        """保存响应"""
        try:
            with open(self.response_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log("error", f"保存响应失败: {e}")
    
    def _load_memory(self) -> Dict:
        """加载长期记忆"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                memory = json.load(f)
                # 限制历史记录大小
                if len(memory.get('history', [])) > 100:
                    memory['history'] = memory['history'][-100:]
                return memory
        return {"history": [], "learnings": [], "context": {}}
    
    def _save_memory(self, memory: Dict):
        """保存长期记忆"""
        # 保存前再次限制
        if len(memory.get('history', [])) > 100:
            memory['history'] = memory['history'][-100:]
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    
    def _log(self, level: str, message: str):
        """写入日志"""
        print(f"[AI循环调度器] [{level.upper()}] {message}")
        self.ipc.write_log("ai_loop", level, message)
    
    def _update_status(self, status: Dict):
        """更新状态"""
        status["pid"] = os.getpid()
        
        # 添加队列状态
        queue_status = self.command_scheduler.get_queue_status()
        status["command_queue"] = queue_status
        
        self.ipc.write_status("ai_loop", status)
    
    def _handle_sigterm(self, signum, frame):
        """处理 SIGTERM 信号"""
        print(f"[AI循环调度器] 收到 SIGTERM 信号，准备退出...")
        self.is_running = False
    
    def _handle_sigint(self, signum, frame):
        """处理 SIGINT 信号"""
        print(f"[AI循环调度器] 收到 SIGINT 信号，准备退出...")
        self.is_running = False


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python ai_loop_scheduler.py <项目根目录> [配置文件]")
        sys.exit(1)
    
    project_root = Path(sys.argv[1])
    config_file = sys.argv[2] if len(sys.argv) > 2 else "config.json"
    
    scheduler = AILoopScheduler(project_root, config_file)
    
    # 注册信号处理
    signal.signal(signal.SIGTERM, scheduler._handle_sigterm)
    signal.signal(signal.SIGINT, scheduler._handle_sigint)
    
    await scheduler.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[AI循环调度器] AI 循环进程已停止")