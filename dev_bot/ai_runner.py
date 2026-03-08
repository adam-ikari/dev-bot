#!/usr/bin/env python3
"""AI 循环运行器 - 简单的核心循环"""

import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from .iflow import IflowCaller
from .interaction_logger import InteractionLogger

logger = logging.getLogger(__name__)


class AIRunner:
    """AI 循环运行器 - 核心循环：while :; cat PROMPT.md | iflow; done
    
    设计原则：
    - 完全交给 iflow 决定，不做任何判断
    - iflow 输出什么指令就执行什么指令
    - 不等待用户回答，AI 自主决策
    """
    
    def __init__(
        self,
        prompt_file: str = "PROMPT.md",
        loop_interval: int = 1,
        timeout: int = 600
    ):
        self.prompt_file = prompt_file
        self.loop_interval = loop_interval
        self.timeout = timeout
        
        # 运行状态
        self.running = False
        self.iteration = 0
        self.restart_pending = False
        
        # 初始化组件
        self.iflow = IflowCaller(timeout=timeout)
        self.ai_logger = InteractionLogger("ai_interactions.log")
    
    async def run(self) -> None:
        """运行核心循环
        
        核心循环：
        while :; do
            cat PROMPT.md | iflow
        done
        
        完全交给 iflow 决定，不做任何判断
        """
        self.running = True
        self.iteration = 0
        
        logger.info("=" * 50)
        logger.info("AI 循环启动")
        logger.info(f"提示词文件: {self.prompt_file}")
        logger.info(f"循环间隔: {self.loop_interval} 秒")
        logger.info(f"超时时间: {self.timeout} 秒")
        logger.info("=" * 50)
        
        try:
            while self.running:
                self.iteration += 1
                start_time = time.time()
                
                # 1. 读取提示词
                prompt = self._read_prompt()
                
                # 2. 调用 iflow
                response = await self.iflow.call(prompt)
                
                # 3. 计算持续时间
                duration = time.time() - start_time
                
                # 4. 执行 iflow 的指令（完全交给 iflow 决定）
                instruction = self._extract_instruction(response)
                if instruction:
                    self._execute_instruction(instruction, response)
                
                # 5. 记录日志
                self.ai_logger.log_interaction(
                    prompt=prompt,
                    response=response,
                    duration=duration
                )
                
                # 6. 输出统计信息（每10次）
                if self.iteration % 10 == 0:
                    stats = self.ai_logger.get_statistics()
                    logger.info(f"📊 统计: {stats}")
                
                # 7. 等待下一次
                if self.running:
                    await asyncio.sleep(self.loop_interval)
        
        except asyncio.CancelledError:
            logger.info("AI 循环接收到停止信号")
        except Exception as e:
            logger.error(f"AI 循环错误: {e}", exc_info=True)
        finally:
            logger.info("AI 循环停止")
            self.running = False
    
    def _read_prompt(self) -> str:
        """读取提示词文件"""
        try:
            with open(self.prompt_file, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"提示词文件不存在: {self.prompt_file}")
            raise
        except Exception as e:
            logger.error(f"读取提示词文件失败: {e}")
            raise
    
    def _extract_instruction(self, response: str) -> str:
        """从 iflow 响应中提取指令
        
        支持的指令：
        - UPDATE_PROMPT: 更新提示词
        - RESTART: 重启以加载新代码
        - STOP: 停止循环
        """
        if "UPDATE_PROMPT:" in response:
            return "UPDATE_PROMPT"
        elif "RESTART" in response:
            return "RESTART"
        elif "STOP" in response:
            return "STOP"
        return None
    
    def _execute_instruction(self, instruction: str, response: str) -> None:
        """执行 iflow 的指令
        
        完全按照 iflow 的指示执行，不做任何判断
        """
        if instruction == "UPDATE_PROMPT":
            new_prompt = self._extract_new_prompt(response)
            if new_prompt:
                self._update_prompt(new_prompt)
                logger.info("✅ 已执行 iflow 指令: UPDATE_PROMPT")
        
        elif instruction == "RESTART":
            logger.info("🔄 已执行 iflow 指令: RESTART")
            self.restart_pending = True
            self.running = False
        
        elif instruction == "STOP":
            logger.info("✅ 已执行 iflow 指令: STOP")
            self.running = False
    
    def _extract_new_prompt(self, response: str) -> str:
        """从响应中提取新提示词"""
        try:
            if "UPDATE_PROMPT:" in response:
                start = response.index("UPDATE_PROMPT:") + len("UPDATE_PROMPT:")
                return response[start:].strip()
            return ""
        except ValueError:
            return ""
    
    def _update_prompt(self, new_prompt: str) -> None:
        """更新提示词文件"""
        try:
            # 备份旧提示词
            if os.path.exists(self.prompt_file):
                backup_file = f"{self.prompt_file}.backup"
                with open(self.prompt_file, "r", encoding="utf-8") as f:
                    with open(backup_file, "w", encoding="utf-8") as bf:
                        bf.write(f.read())
                logger.info(f"💾 已备份旧提示词到 {backup_file}")
            
            # 写入新提示词
            with open(self.prompt_file, "w", encoding="utf-8") as f:
                f.write(new_prompt)
            
            logger.info(f"✅ 提示词已更新到 {self.prompt_file}")
        
        except Exception as e:
            logger.error(f"更新提示词失败: {e}")
    
    
    
    def stop(self) -> None:
        """停止 AI 循环"""
        self.running = False
        logger.info("AI 循环停止信号已发送")
    
    def get_status(self) -> dict:
        """获取运行状态"""
        return {
            "running": self.running,
            "iteration": self.iteration,
            "restart_pending": self.restart_pending,
            "prompt_file": self.prompt_file,
            "loop_interval": self.loop_interval
        }
