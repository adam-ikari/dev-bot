#!/usr/bin/env python3
"""
Dev-Bot 分层架构

提供分层架构设计：
- AI 守护程序（最底层，不可变）
- 业务逻辑层（上层，可变）
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any


class AIGuardian:
    """AI 守护程序 - 最底层（不可变）
    
    持续监控 Dev-Bot 运行状态，自动检测问题并恢复
    """
    
    def __init__(self, ai_command: str = "iflow", check_interval: int = 30):
        self.ai_command = ai_command
        self.check_interval = check_interval  # 检查间隔（秒）
        self.recovery_count = 0
        self.last_check_time = None
        self.is_running = False
        self._task = None
        
    async def start(self):
        """启动守护程序"""
        if self.is_running:
            print("[AI 守护] 守护程序已在运行")
            return
        
        self.is_running = True
        print(f"[AI 守护] 启动守护程序（检查间隔: {self.check_interval}秒）")
        
        # 创建后台任务
        self._task = asyncio.create_task(self._guard_loop())
        
    async def stop(self):
        """停止守护程序"""
        if not self.is_running:
            return
        
        self.is_running = False
        print("[AI 守护] 停止守护程序")
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _guard_loop(self):
        """守护循环"""
        while self.is_running:
            try:
                # 检查系统状态
                await self._check_system_status()
                
                # 等待下次检查
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[AI 守护] 守护循环出错: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_system_status(self):
        """检查系统状态"""
        self.last_check_time = time.time()
        
        print(f"[AI 守护] 检查系统状态... (第 {self.recovery_count + 1} 次检查)")
        
        # 1. 读取终端内容
        terminal_file = await self._read_terminal()
        if not terminal_file:
            print("[AI 守护] 无法读取终端内容，跳过检查")
            return
        
        # 2. 分析终端状态
        needs_recovery = await self._analyze_terminal(terminal_file)
        
        # 3. 如果需要恢复，执行恢复
        if needs_recovery:
            print("[AI 守护] 检测到问题，开始恢复...")
            await self._perform_recovery()
        else:
            print("[AI 守护] 系统状态正常")
    
    async def _read_terminal(self) -> Optional[Path]:
        """读取终端内容"""
        try:
            # 创建日志目录
            log_dir = Path(".ai-terminal-logs")
            log_dir.mkdir(exist_ok=True)
            
            # 生成文件名
            timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
            terminal_file = log_dir / f"terminal_{timestamp}.txt"
            
            # 读取 shell 历史
            result = await asyncio.create_subprocess_exec(
                "bash", "-c", "history",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if stdout:
                terminal_content = stdout.decode()
            else:
                # 备用方法：读取 bash 历史
                history_file = Path.home() / ".bash_history"
                if history_file.exists():
                    with open(history_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    terminal_content = ''.join(lines[-50:])
                else:
                    terminal_content = "# 终端内容为空"
            
            # 保存到文件
            with open(terminal_file, 'w', encoding='utf-8') as f:
                f.write(terminal_content)
            
            return terminal_file
            
        except Exception as e:
            print(f"[AI 守护] 读取终端失败: {e}")
            return None
    
    async def _analyze_terminal(self, terminal_file: Path) -> bool:
        """分析终端状态"""
        try:
            # 读取终端内容
            with open(terminal_file, 'r', encoding='utf-8') as f:
                terminal_content = f.read()
            
            # 构建提示词
            prompt = f"""你是 Dev-Bot 的 AI 守护系统（最底层兜底）。

当前终端内容：
```text
{terminal_content}
```

你的任务是：
1. 分析终端内容，判断 Dev-Bot 是否正常运行
2. 如果 Dev-Bot 出现错误、卡住或终止，立即报告需要恢复
3. 如果 Dev-Bot 运行正常，报告状态正常

请输出你的判断（只需要一句话）：
- 如果需要恢复，输出："需要恢复：[问题描述]"
- 如果状态正常，输出："状态正常"

不要执行任何操作，只做判断。"""
            
            # 调用 iflow
            result = await asyncio.create_subprocess_exec(
                self.ai_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                result.communicate(input=prompt.encode()),
                timeout=30
            )
            
            response = (stdout + stderr).decode().strip()
            
            # 判断是否需要恢复
            if "需要恢复" in response or "错误" in response or "卡住" in response:
                print(f"[AI 守护] AI 判断需要恢复: {response}")
                return True
            else:
                print(f"[AI 守护] AI 判断状态正常: {response}")
                return False
            
        except asyncio.TimeoutError:
            print("[AI 守护] AI 分析超时，假设状态正常")
            return False
        except Exception as e:
            print(f"[AI 守护] 分析终端异常: {e}")
            return False
    
    async def _perform_recovery(self):
        """执行恢复操作"""
        try:
            prompt = """你是 Dev-Bot 的 AI 守护系统（最底层兜底）。

Dev-Bot 出现了问题，需要你立即执行恢复操作。

你的任务是：
1. 分析当前系统状态
2. 执行必要的恢复操作：
   - 如果遇到错误提示，按 Esc 关闭
   - 如果程序卡住，按 Ctrl+C 退出
   - 如果程序终止，重新启动 Dev-Bot
3. 你有完整的系统访问权限

请执行恢复操作，然后报告结果。"""
            
            # 调用 iflow 执行恢复
            result = await asyncio.create_subprocess_exec(
                self.ai_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                result.communicate(input=prompt.encode()),
                timeout=60
            )
            
            response = (stdout + stderr).decode()
            
            # 记录恢复
            self.recovery_count += 1
            print(f"[AI 守护] 恢复操作完成（第 {self.recovery_count} 次）")
            print(f"[AI 守护] AI 响应: {response[:200]}")
            
        except asyncio.TimeoutError:
            print("[AI 守护] 恢复操作超时")
        except Exception as e:
            print(f"[AI 守护] 恢复操作失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "is_running": self.is_running,
            "recovery_count": self.recovery_count,
            "last_check_time": self.last_check_time,
            "check_interval": self.check_interval,
            "ai_command": self.ai_command
        }


class BusinessLogicLayer:
    """业务逻辑层 - 上层（可变）"""
    
    def __init__(self):
        self.tasks = []
        
    def add_task(self, task: str):
        """添加任务"""
        self.tasks.append(task)
    
    def get_tasks(self) -> List[str]:
        """获取任务列表"""
        return self.tasks
    
    def execute_tasks(self):
        """执行任务"""
        print(f"[业务逻辑层] 执行 {len(self.tasks)} 个任务...")
        for task in self.tasks:
            print(f"[业务逻辑层] 执行: {task}")


def get_architecture() -> Dict[str, Any]:
    """获取架构实例
    
    Returns:
        架构字典
    """
    return {
        "ai_guardian": AIGuardian(),
        "business_logic_layer": BusinessLogicLayer(),
        "architecture": {
            "version": "3.0",
            "guarantee": "AI 守护程序作为最底层兜底，持续监控并自动恢复"
        }
    }


def get_architecture_status() -> Dict[str, Any]:
    """获取架构状态
    
    Returns:
        状态字典
    """
    guardian = AIGuardian()
    
    return {
        "ai_guardian": {
            "status": "ready",
            "check_interval": guardian.check_interval,
            "recovery_count": guardian.recovery_count
        },
        "business_logic_layer": {
            "status": "active",
            "tasks": []
        },
        "architecture": {
            "version": "3.0",
            "guarantee": "AI 守护程序作为最底层兜底，持续监控并自动恢复"
        }
    }
