#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dev-Bot Core - 极简核心调度器

类似 OpenOAI 的极简实现：
- 只负责调用 iflow
- 不实现任何具体功能
- 提供统一的调用接口
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List


class DevBotCore:
    """Dev-Bot 核心调度器
    
    极简设计：只负责调用 iflow，不实现任何业务逻辑
    """
    
    def __init__(self, iflow_command: str = "iflow"):
        self.iflow_command = iflow_command
        self.config_file = Path.cwd() / "config.json"
        
        # 加载配置
        self.config = self._load_config()
        
        print(f"[Dev-Bot] 核心初始化完成")
        print(f"[Dev-Bot] iflow 命令: {self.iflow_command}")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"iflow_command": "iflow"}
    
    async def call_iflow(
        self,
        prompt: str,
        mode: str = "",
        timeout: int = 300
    ) -> Dict[str, Any]:
        """调用 iflow
        
        Args:
            prompt: 提示词
            mode: iflow 模式（--plan, -y, --thinking）
            timeout: 超时时间
        
        Returns:
            调用结果
        """
        import time
        start_time = time.time()
        
        # 构建命令
        cmd = [self.iflow_command]
        if mode:
            cmd.append(mode)
        
        try:
            # 创建进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            # 发送提示词
            process.stdin.write(prompt.encode())
            process.stdin.write_eof()
            
            # 等待完成
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='ignore'),
                "error": stderr.decode('utf-8', errors='ignore'),
                "exit_code": process.returncode,
                "duration": duration
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "output": "",
                "error": f"调用超时（{timeout}秒）",
                "exit_code": -1,
                "duration": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "exit_code": -1,
                "duration": time.time() - start_time
            }
    
    async def plan(self, prompt: str, timeout: int = 300) -> Dict[str, Any]:
        """规划模式（--plan）"""
        return await self.call_iflow(prompt, "--plan", timeout)
    
    async def execute(self, prompt: str, timeout: int = 600) -> Dict[str, Any]:
        """执行模式（-y）"""
        return await self.call_iflow(prompt, "-y", timeout)
    
    async def think(self, prompt: str, timeout: int = 600) -> Dict[str, Any]:
        """思考模式（--thinking）"""
        return await self.call_iflow(prompt, "--thinking", timeout)
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "iflow_command": self.iflow_command,
            "config_file": str(self.config_file),
            "config": self.config
        }


# 全局核心实例
_global_core = None


def get_core(iflow_command: str = "iflow") -> DevBotCore:
    """获取全局核心实例"""
    global _global_core
    
    if _global_core is None:
        _global_core = DevBotCore(iflow_command)
    
    return _global_core


def reset_core():
    """重置全局核心"""
    global _global_core
    _global_core = None