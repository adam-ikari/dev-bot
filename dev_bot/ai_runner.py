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
    """AI 循环运行器 - 核心循环：while :; cat PROMPT.md | iflow; done"""
    
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
        
        # 代码文件监控
        self.code_files_mtimes = {}
        self.code_reload_count = 0
    
    async def run(self) -> None:
        """运行核心循环
        
        核心循环：
        while :; do
            cat PROMPT.md | iflow
        done
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
                
                # 4. 检查指令
                prompt_updated = self._check_update_prompt(response)
                code_modified = self._check_restart(response)
                should_stop = self._check_stop(response)
                
                # 5. 记录日志
                self.ai_logger.log_interaction(
                    prompt=prompt,
                    response=response,
                    duration=duration,
                    prompt_updated=prompt_updated,
                    code_modified=code_modified
                )
                
                # 6. 检查代码变化
                if self._check_code_changes():
                    logger.info("🔄 检测到代码变化，准备重启...")
                    self.restart_pending = True
                    self.running = False
                    break
                
                # 7. 检查是否停止
                if should_stop:
                    logger.info("✅ iflow 要求停止")
                    self.running = False
                    break
                
                # 8. 检查是否重启
                if code_modified:
                    logger.info("🔄 iflow 要求重启以加载新代码")
                    self.restart_pending = True
                    self.running = False
                    break
                
                # 9. 输出统计信息（每10次）
                if self.iteration % 10 == 0:
                    stats = self.ai_logger.get_statistics()
                    logger.info(f"📊 统计: {stats}")
                
                # 10. 等待下一次
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
    
    def _check_update_prompt(self, response: str) -> bool:
        """检查是否需要更新提示词"""
        if "UPDATE_PROMPT:" in response or "优化提示词" in response:
            new_prompt = self._extract_new_prompt(response)
            if new_prompt:
                self._update_prompt(new_prompt)
                logger.info("✅ 提示词已更新")
                return True
        return False
    
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
    
    def _check_restart(self, response: str) -> bool:
        """检查是否需要重启"""
        return "RESTART" in response or "代码已修改" in response
    
    def _check_stop(self, response: str) -> bool:
        """检查是否需要停止"""
        return "STOP" in response or "任务完成" in response
    
    def _check_code_changes(self) -> bool:
        """检查代码文件是否有变化"""
        changes_detected = False
        
        # 扫描 dev_bot 目录
        for root, dirs, files in os.walk("dev_bot"):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    filepath = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(filepath)
                        
                        if filepath in self.code_files_mtimes:
                            if mtime > self.code_files_mtimes[filepath]:
                                logger.info(f"📝 检测到文件修改: {filepath}")
                                changes_detected = True
                        
                        self.code_files_mtimes[filepath] = mtime
                    
                    except OSError:
                        pass
        
        return changes_detected
    
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
