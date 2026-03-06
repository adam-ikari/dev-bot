#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iFlow 调用管理器

管理 AI 循环与 iflow 的交互，提供统一的调用接口
"""

import asyncio
import json
import os
import signal
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from dev_bot.process_manager import ProcessManager


class IFlowMode(Enum):
    """iFlow 调用模式"""
    PLAN = "--plan"  # 只做计划，不执行
    YOLO = "-y"  # yolo 模式，无需授权
    THINKING = "--thinking"  # 思考模式，更全面
    NORMAL = ""  # 普通模式


class IFlowCallResult:
    """iFlow 调用结果"""
    
    def __init__(
        self,
        success: bool,
        output: str,
        error: str = "",
        exit_code: Optional[int] = None,
        duration: float = 0.0
    ):
        self.success = success
        self.output = output
        self.error = error
        self.exit_code = exit_code
        self.duration = duration
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "duration": self.duration
        }


class IFlowManager:
    """iFlow 调用管理器
    
    管理 AI 循环与 iflow 的交互
    """
    
    def __init__(
        self,
        iflow_command: str = "iflow",
        default_timeout: int = 300,
        max_retries: int = 3
    ):
        self.iflow_command = iflow_command
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.process_manager = ProcessManager()
        
        # 调用统计
        self.call_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_duration = 0.0
        
        print(f"[iFlow管理器] 初始化完成")
        print(f"[iFlow管理器] 命令: {iflow_command}")
        print(f"[iFlow管理器] 默认超时: {default_timeout}秒")
    
    async def call(
        self,
        prompt: str,
        mode: IFlowMode = IFlowMode.NORMAL,
        timeout: Optional[int] = None,
        retries: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> IFlowCallResult:
        """调用 iflow
        
        Args:
            prompt: 提示词
            mode: 调用模式
            timeout: 超时时间（秒）
            retries: 重试次数
            context: 上下文信息
        
        Returns:
            调用结果
        """
        # 设置默认值
        actual_timeout = timeout or self.default_timeout
        actual_retries = retries if retries is not None else self.max_retries
        
        # 构建命令
        args = []
        if mode.value:
            args.append(mode.value)
        
        # 添加上下文到提示词
        final_prompt = self._build_prompt(prompt, context)
        
        # 尝试调用
        last_error = None
        for attempt in range(actual_retries + 1):
            try:
                self.call_count += 1
                start_time = time.time()
                
                result = await self._execute_iflow(
                    final_prompt,
                    args,
                    actual_timeout
                )
                
                duration = time.time() - start_time
                self.total_duration += duration
                
                if result.success:
                    self.success_count += 1
                    result.duration = duration
                    return result
                else:
                    self.failure_count += 1
                    last_error = result.error
                    
                    if attempt < actual_retries:
                        print(f"[iFlow管理器] 调用失败，重试 {attempt + 1}/{actual_retries}...")
                        await asyncio.sleep(1)
            
            except asyncio.TimeoutError:
                self.failure_count += 1
                last_error = f"调用超时（{actual_timeout}秒）"
                
                if attempt < actual_retries:
                    print(f"[iFlow管理器] 调用超时，重试 {attempt + 1}/{actual_retries}...")
                    await asyncio.sleep(1)
            
            except Exception as e:
                self.failure_count += 1
                last_error = str(e)
                
                if attempt < actual_retries:
                    print(f"[iFlow管理器] 调用异常，重试 {attempt + 1}/{actual_retries}: {e}")
                    await asyncio.sleep(1)
        
        # 所有重试都失败
        return IFlowCallResult(
            success=False,
            output="",
            error=last_error or "调用失败",
            duration=0.0
        )
    
    async def call_plan(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 300
    ) -> IFlowCallResult:
        """调用 iflow --plan（只做计划）"""
        return await self.call(
            prompt=prompt,
            mode=IFlowMode.PLAN,
            timeout=timeout,
            context=context
        )
    
    async def call_yolo(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 600
    ) -> IFlowCallResult:
        """调用 iflow -y（yolo 模式，无需授权）"""
        return await self.call(
            prompt=prompt,
            mode=IFlowMode.YOLO,
            timeout=timeout,
            context=context
        )
    
    async def call_thinking(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 600
    ) -> IFlowCallResult:
        """调用 iflow --thinking（思考模式）"""
        return await self.call(
            prompt=prompt,
            mode=IFlowMode.THINKING,
            timeout=timeout,
            context=context
        )
    
    async def _execute_iflow(
        self,
        prompt: str,
        args: List[str],
        timeout: int
    ) -> IFlowCallResult:
        """执行 iflow 命令
        
        Args:
            prompt: 提示词
            args: 命令参数
            timeout: 超时时间
        
        Returns:
            调用结果
        """
        try:
            # 创建进程
            process = await asyncio.create_subprocess_exec(
                self.iflow_command,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            # 发送提示词
            process.stdin.write(prompt.encode())
            process.stdin.write_eof()
            
            # 等待完成（带超时）
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                output = stdout.decode('utf-8', errors='ignore')
                error = stderr.decode('utf-8', errors='ignore')
                
                return IFlowCallResult(
                    success=process.returncode == 0,
                    output=output,
                    error=error,
                    exit_code=process.returncode
                )
            
            except asyncio.TimeoutError:
                # 超时，终止进程
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                
                raise
            
        except FileNotFoundError:
            return IFlowCallResult(
                success=False,
                output="",
                error=f"iflow 命令未找到: {self.iflow_command}",
                exit_code=-1
            )
        except Exception as e:
            return IFlowCallResult(
                success=False,
                output="",
                error=f"执行 iflow 时出错: {e}",
                exit_code=-1
            )
    
    def _build_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建完整提示词
        
        Args:
            prompt: 基础提示词
            context: 上下文信息
        
        Returns:
            完整提示词
        """
        if not context:
            return prompt
        
        # 添加上下文信息
        context_str = json.dumps(context, indent=2, ensure_ascii=False)
        
        full_prompt = f"""# 上下文信息

```json
{context_str}
```

---
{prompt}
---
"""
        
        return full_prompt
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取调用统计
        
        Returns:
            统计信息
        """
        success_rate = 0.0
        if self.call_count > 0:
            success_rate = self.success_count / self.call_count
        
        avg_duration = 0.0
        if self.success_count > 0:
            avg_duration = self.total_duration / self.success_count
        
        return {
            "call_count": self.call_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": success_rate,
            "total_duration": self.total_duration,
            "average_duration": avg_duration
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.call_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_duration = 0.0


# 全局 iflow 管理器实例
_global_iflow_manager = None


def get_iflow_manager(
    iflow_command: str = "iflow",
    default_timeout: int = 300,
    max_retries: int = 3
) -> IFlowManager:
    """获取全局 iflow 管理器实例
    
    Args:
        iflow_command: iflow 命令
        default_timeout: 默认超时
        max_retries: 最大重试次数
    
    Returns:
        全局 iflow 管理器实例
    """
    global _global_iflow_manager
    
    if _global_iflow_manager is None:
        _global_iflow_manager = IFlowManager(
            iflow_command=iflow_command,
            default_timeout=default_timeout,
            max_retries=max_retries
        )
    
    return _global_iflow_manager


def reset_iflow_manager():
    """重置全局 iflow 管理器（主要用于测试）"""
    global _global_iflow_manager
    _global_iflow_manager = None