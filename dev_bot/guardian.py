#!/usr/bin/env python3
"""Dev-Bot 守护系统 - 进程监控和健康检查"""

import asyncio
import psutil
import logging
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from textual.widgets import RichLog

# 配置日志系统
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 文件处理器（始终启用）
file_handler = logging.FileHandler('guardian.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# TUI 日志处理器（如果可用）
_tui_handler = None

def setup_tui_logging(app):
    """设置 TUI 日志输出
    
    Args:
        app: TUI 应用实例
    """
    global _tui_handler
    
    class TUILogHandler(logging.Handler):
        """自定义日志处理器，将日志输出到TUI log_view"""
        
        def __init__(self, app):
            super().__init__()
            self.app = app
        
        def emit(self, record):
            try:
                # 只在组件已挂载时输出日志
                if not hasattr(self.app, "_components_mounted"):
                    return
                
                log_view = self.app.query_one("#log-view", RichLog)
                if log_view is None:
                    return
                
                # 格式化日志消息（简化格式）
                msg = record.getMessage()
                
                # 根据日志级别设置前缀
                if record.levelno >= logging.ERROR:
                    log_view.write(f"[red]ERROR: {msg}[/red]")
                elif record.levelno >= logging.WARNING:
                    log_view.write(f"[yellow]WARNING: {msg}[/yellow]")
                elif record.levelno >= logging.INFO:
                    log_view.write(f"[green]INFO: {msg}[/green]")
                else:
                    log_view.write(f"[dim]DEBUG: {msg}[/dim]")
            except Exception:
                pass  # 避免日志处理器本身出错
    
    # 移除旧的 TUI 处理器
    if _tui_handler:
        logger.removeHandler(_tui_handler)
    
    # 添加新的 TUI 处理器
    _tui_handler = TUILogHandler(app)
    _tui_handler.setLevel(logging.INFO)
    logger.addHandler(_tui_handler)

# 历史日志处理器（记录重要事件到历史文件）
_history_handler = None

def setup_history_logging():
    """设置历史日志记录
    
    记录重要的日志事件到历史文件中
    """
    global _history_handler
    
    try:
        from dev_bot import get_memory_system
        memory_system = get_memory_system()
        
        class HistoryLogHandler(logging.Handler):
            """自定义日志处理器，将重要日志记录到历史"""
            
            def __init__(self):
                super().__init__()
                self.memory_system = get_memory_system()
            
            def emit(self, record):
                try:
                    # 只记录重要级别的事件
                    if record.levelno < logging.INFO:
                        return
                    
                    # 获取日志消息
                    msg = record.getMessage()
                    
                    # 记录到历史
                    entry_type = "log_info"
                    if record.levelno >= logging.ERROR:
                        entry_type = "log_error"
                    elif record.levelno >= logging.WARNING:
                        entry_type = "log_warning"
                    
                    # 添加历史记录
                    self.memory_system.add_history_entry(
                        entry_type,
                        f"{record.name}: {msg[:100]}",
                        msg[:200] if msg else ""
                    )
                except Exception:
                    pass  # 避免日志处理器本身出错
        
        # 移除旧的历史日志处理器
        if _history_handler:
            logger.removeHandler(_history_handler)
        
        # 添加新的历史日志处理器
        _history_handler = HistoryLogHandler()
        _history_handler.setLevel(logging.INFO)
        logger.addHandler(_history_handler)
        
    except ImportError:
        pass


class Guardian:
    """守护系统 - 统一管理所有 AI 循环进程"""
    
    def __init__(
        self,
        check_interval: int = 30,
        memory_threshold: int = 80,  # 80%
        cpu_threshold: int = 90,  # 90%
        disk_threshold: int = 90,  # 90%
        max_restarts: int = 5,
        restart_delay: int = 10,
        ai_loop_interval: int = 1  # AI 循环间隔（秒）
    ):
        self.check_interval = check_interval
        self.memory_threshold = memory_threshold
        self.cpu_threshold = cpu_threshold
        self.disk_threshold = disk_threshold
        self.max_restarts = max_restarts
        self.restart_delay = restart_delay
        self.ai_loop_interval = ai_loop_interval
        
        # 进程管理
        self.running = False
        self.restart_count = 0
        
        # AI 循环管理
        self.ai_loop_running = False
        self.ai_loop_task = None
        self.ai_loop_iteration = 0
        
        # AI 修复
        self.iflow = None  # AI 呼叫器
        
        # 代码热重载管理
        self.enable_code_reload = True  # 是否启用代码热重载
        self.code_reload_check_interval = 5  # 代码检查间隔（秒）
        self.code_files_mtimes = {}  # 记录代码文件的修改时间
        self.code_reload_count = 0  # 代码重载次数
        self.code_reload_pending = False  # 是否有待处理的代码重载
        
        # 动态提示词管理
        self.enable_dynamic_prompt = True  # 是否启用动态提示词
        self.current_prompt = None  # 当前使用的提示词
        self.prompt_version = 1  # 提示词版本
        self.prompt_history = []  # 提示词修改历史
        self.base_prompt_template = None  # 基础提示词模板
        
        # 两阶段循环管理
        self.current_phase = "execution"  # 当前阶段: execution/review
        self.execution_iteration = 0  # 执行阶段迭代次数
        self.review_iteration = 0  # 复盘阶段迭代次数
        self.total_cycles = 0  # 总循环次数（执行+复盘）
        
        # 执行状态管理
        self.execution_state = {
            "current_task": None,  # 当前任务
            "task_steps": [],  # 任务步骤
            "completed_steps": [],  # 已完成的步骤
            "total_tasks": 0,  # 总任务数
            "completed_tasks": 0,  # 已完成任务数
            "work_summary": ""  # 工作摘要
        }
        
        # 执行配置
        self.max_execution_iterations = 20  # 最大执行迭代次数（增加）
        self.min_tasks_per_execution = 3  # 每次执行最少完成任务数
        self.execution_timeout = 300  # 执行阶段超时时间（5分钟）
        self.execution_start_time = None  # 执行阶段开始时间
        self.last_activity_time = None  # 最后活动时间（用于检测真正的超时）
        
        # 功能完成跟踪
        self.feature_completed = False  # 功能是否完成
        self.restart_pending = False  # 是否待重启
    
    def run_process(self, command: list[str], redirect_output: bool = True) -> None:
        """运行并监控进程（完整的进程生命周期管理）

        Args:
            command: 要执行的命令列表
            redirect_output: 是否重定向 stdout/stderr，TUI 模式设为 False 以直接显示界面
        """
        import subprocess
        import signal
        from datetime import datetime

        logger.info("=" * 50)
        logger.info("AI 守护系统启动")
        logger.info(f"最大重启次数: {self.max_restarts}")
        logger.info(f"重启延迟: {self.restart_delay} 秒")
        logger.info(f"检查间隔: {self.check_interval} 秒")
        logger.info(f"重定向输出: {redirect_output}")
        logger.info("=" * 50)

        self.restart_count = 0
        process = None

        # 设置信号处理器
        def signal_handler(signum, frame):
            logger.info(f"接收到信号 {signum}")
            if process and process.poll() is None:
                logger.info("正在停止子进程...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("子进程未响应，强制终止...")
                    process.kill()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        while self.restart_count < self.max_restarts:
            attempt = self.restart_count + 1
            logger.info(f"\n启动 Dev-Bot (尝试 {attempt}/{self.max_restarts})")
            logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"命令: {' '.join(command)}")

            try:
                # 准备进程参数
                popen_kwargs = {"text": True}
                if redirect_output:
                    # 重定向输出以便捕获错误信息
                    popen_kwargs["stdout"] = subprocess.PIPE
                    popen_kwargs["stderr"] = subprocess.PIPE
                else:
                    # 不重定向输出，让进程直接控制终端（用于 TUI）
                    popen_kwargs["stdout"] = None
                    popen_kwargs["stderr"] = None

                # 使用 Popen 以便更好地控制进程
                process = subprocess.Popen(command, **popen_kwargs)
                logger.info(f"子进程 PID: {process.pid}")
                
                # 等待进程结束
                returncode = process.wait()
                
                # 正常退出，重置计数器
                if returncode == 0:
                    logger.info("Dev-Bot 正常退出")
                    self.restart_count = 0
                    break
                else:
                    logger.error(f"Dev-Bot 异常退出，返回码: {returncode}")
                    # 记录错误输出
                    if process.stdout:
                        stdout = process.stdout.read()
                        if stdout:
                            logger.error(f"stdout: {stdout}")
                    if process.stderr:
                        stderr = process.stderr.read()
                        if stderr:
                            logger.error(f"stderr: {stderr}")
                    self._handle_crash()
            
            except KeyboardInterrupt:
                logger.info("\n接收到中断信号，停止守护")
                if process and process.poll() is None:
                    process.terminate()
                break
            
            except Exception as e:
                logger.error(f"未预期的错误: {e}", exc_info=True)
                self._handle_crash()
        
        if self.restart_count >= self.max_restarts:
            logger.error(f"\n达到最大重启次数 ({self.max_restarts})，停止尝试")
            logger.error("请检查错误日志并手动解决问题")
    
    def _handle_crash(self) -> None:
        """处理崩溃 - 尝试 AI 智能修复"""
        import time
        
        self.restart_count += 1
        
        if self.restart_count < self.max_restarts:
            logger.info(f"\n🔧 尝试 AI 智能修复...")
            logger.info(f"当前重启计数: {self.restart_count}/{self.max_restarts}")
            
            # 尝试 AI 修复
            fixed = self.try_auto_fix()
            
            if fixed:
                logger.info("✅ AI 修复成功，准备重启...")
            else:
                logger.warning("⚠️ AI 修复失败，将尝试简单重启...")
            
            logger.info(f"将在 {self.restart_delay} 秒后重启...")
            time.sleep(self.restart_delay)
        else:
            logger.error("已达到最大重启次数，不再尝试")
    
    async def start(self, monitored_pid: Optional[int] = None) -> None:
        """启动守护"""
        self.running = True
        logger.info("=" * 50)
        logger.info("守护系统启动")
        logger.info(f"检查间隔: {self.check_interval} 秒")
        logger.info(f"内存阈值: {self.memory_threshold}%")
        logger.info(f"CPU 阈值: {self.cpu_threshold}%")
        logger.info(f"磁盘阈值: {self.disk_threshold}%")
        logger.info("=" * 50)
        
        if monitored_pid:
            logger.info(f"监控进程 PID: {monitored_pid}")
        else:
            logger.info("监控自身进程")
        
        try:
            while self.running:
                await self.check_health(monitored_pid)
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("守护系统已停止")
        except Exception as e:
            logger.error(f"守护系统错误: {e}")
    
    async def check_health(self, monitored_pid: Optional[int] = None) -> None:
        """检查健康状态"""
        try:
            process = psutil.Process(monitored_pid) if monitored_pid else psutil.Process()
            
            # 检查内存使用
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            if memory_percent > self.memory_threshold:
                logger.warning(f"⚠️  内存使用过高: {memory_percent:.1f}%")
            
            # 检查 CPU 使用
            cpu_percent = process.cpu_percent(interval=1)
            if cpu_percent > self.cpu_threshold:
                logger.warning(f"⚠️  CPU 使用过高: {cpu_percent:.1f}%")
            
            # 检查磁盘使用
            disk_usage = psutil.disk_usage('/')
            disk_percent = disk_usage.percent
            if disk_percent > self.disk_threshold:
                logger.warning(f"⚠️  磁盘使用过高: {disk_percent:.1f}%")
            
            # 记录健康状态
            logger.info(
                f"✅ 健康检查 - PID: {process.pid}, "
                f"内存: {memory_percent:.1f}%, "
                f"CPU: {cpu_percent:.1f}%, "
                f"磁盘: {disk_percent:.1f}%"
            )
        
        except psutil.NoSuchProcess:
            logger.error(f"❌ 进程不存在: PID {monitored_pid}")
            if monitored_pid:
                logger.info("进程已终止，守护系统停止")
                self.running = False
        
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
    
    def stop(self) -> None:
        """停止守护"""
        self.running = False
        logger.info("守护系统停止信号已发送")
    
    async def run_ai_loop(self) -> None:
        """运行 AI 循环（持久的 iflow 会话，执行→复盘循环）"""
        from dev_bot import IflowSession, get_memory_system
        from dev_bot.iflow import (
            IflowError,
            IflowTimeoutError,
            IflowProcessError,
            IflowTokenExpiredError,
            IflowMemoryError
        )
        from pathlib import Path
        import os

        self.ai_loop_running = True
        self.ai_loop_iteration = 0

        # 初始化记忆系统
        memory_system = get_memory_system()
        memory = memory_system.load_context()

        # 初始化持久的 IflowSession
        iflow_session = IflowSession(timeout=600)  # 10分钟超时

        # 初始化提示词系统
        self.initialize_prompt_template()

        # 执行结果存储（用于复盘阶段）
        execution_results = []

        logger.info("=" * 50)
        logger.info("AI 循环进程启动（持久的 iflow 会话）")
        logger.info(f"循环间隔: {self.ai_loop_interval} 秒")
        logger.info("=" * 50)

        # 记录启动到历史
        memory_system.add_history_entry("ai_loop_start", "AI 循环启动（持久会话）")

        try:
            # 启动 iflow 会话
            await iflow_session.start()

            while self.ai_loop_running:
                self.ai_loop_iteration += 1

                # 检查是否需要重启（功能完成且待重启）
                if self.restart_pending:
                    logger.info("🔄 功能已完成，准备重启以加载新代码")
                    logger.info("💾 保存当前状态并重启...")
                    # 保存状态
                    memory_system.save_context({
                        "restart_pending": True,
                        "feature_completed": True,
                        "last_iteration": self.ai_loop_iteration,
                        "last_update": datetime.now().isoformat()
                    })
                    # 停止循环和会话
                    self.ai_loop_running = False
                    await iflow_session.stop()
                    break

                if self.current_phase == "execution":
                    # ============ 执行阶段 ============
                    logger.info(f"=== 执行阶段 {self.execution_iteration} ===")

                    # 首次进入执行阶段，设置开始时间
                    if self.execution_start_time is None:
                        self.execution_start_time = datetime.now()
                        self.last_activity_time = datetime.now()
                        logger.info(f"⏱️ 执行阶段开始计时: {self.execution_start_time.strftime('%H:%M:%S')}")

                    # 检查执行阶段超时（基于最后活动时间）
                    if self.last_activity_time:
                        inactive_time = (datetime.now() - self.last_activity_time).total_seconds()
                        if inactive_time > self.execution_timeout:
                            logger.warning(f"⚠️ 执行阶段无活动超时 ({inactive_time:.0f}s > {self.execution_timeout}s)，进入复盘")
                            memory_system.add_history_entry("warning", f"执行阶段无活动超时: {inactive_time:.0f}秒")
                            self.switch_phase("review")
                            continue

                    # 更新活动时间
                    self.last_activity_time = datetime.now()

                    # 构建执行阶段提示词
                    memory_summary = memory_system.get_context_summary()
                    prompt = self.build_execution_prompt(memory_summary)

                    try:
                        result = await iflow_session.send(prompt)
                        logger.info(f"执行阶段 {self.execution_iteration} 完成")

                        # 增加执行迭代计数
                        self.execution_iteration += 1

                        # 保存执行结果
                        execution_results.append({
                            "iteration": self.execution_iteration,
                            "result": result,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # 解析 AI 输出中的指令
                        self._process_prompt_commands(result)
                        
                        # 检查 AI 是否要求进入复盘阶段
                        if "[进入复盘]" in result:
                            logger.info("🔄 AI 要求进入复盘阶段")
                            self.switch_phase("review")
                        else:
                            logger.info("📋 继续执行阶段，等待 AI 完成")
                        
                        # 记录到历史
                        memory_system.add_history_entry(
                            "execution_phase",
                            f"执行阶段 {self.execution_iteration}",
                            result[:200] if result else ""
                        )
                        
                    except IflowTimeoutError as e:
                        logger.error(f"执行阶段超时错误: {e}")
                        memory_system.add_history_entry("error", f"执行阶段超时: {e}")
                    except IflowProcessError as e:
                        logger.error(f"执行阶段进程错误: {e}")
                        memory_system.add_history_entry("error", f"执行阶段进程错误: {e}")
                    except IflowTokenExpiredError as e:
                        logger.error(f"❌ iflow 令牌过期: {e}")
                        memory_system.add_history_entry("error", f"令牌过期: {e}")
                        self.ai_loop_running = False
                        break
                    except IflowMemoryError as e:
                        logger.error(f"❌ iflow 内存错误: {e}")
                        memory_system.add_history_entry("error", f"内存错误: {e}")
                        self.ai_loop_running = False
                        break
                    except IflowError as e:
                        logger.error(f"执行阶段 Iflow 错误: {e}")
                        memory_system.add_history_entry("error", f"执行阶段错误: {e}")
                    except Exception as e:
                        logger.error(f"执行阶段未知错误: {e}", exc_info=True)
                        memory_system.add_history_entry("error", f"执行阶段未知错误: {e}")
                
                elif self.current_phase == "review":
                    # ============ 复盘阶段 ============
                    logger.info(f"=== 复盘阶段 {self.review_iteration} ===")
                    
                    # 构建复盘阶段提示词
                    memory_summary = memory_system.get_context_summary()
                    
                    # 汇总执行结果（传递更多上下文）
                    execution_summary_parts = []
                    for i, res in enumerate(execution_results):
                        result_preview = res['result'][:200] + "..." if len(res['result']) > 200 else res['result']
                        execution_summary_parts.append(
                            f"执行迭代 {i+1} (时间: {res['timestamp']}):\n"
                            f"{result_preview}"
                        )
                    
                    execution_summary = "\\n\\n".join(execution_summary_parts)
                    
                    # 添加执行状态信息
                    if self.execution_state.get("work_summary"):
                        execution_summary += f"\\n\\n工作摘要:\\n{self.execution_state['work_summary']}"
                    
                    prompt = self.build_review_prompt(memory_summary, execution_summary)
                    
                    try:
                        result = await iflow_session.send(prompt)
                        logger.info(f"复盘阶段 {self.review_iteration} 完成")
                        
                        # 解析 AI 输出中的指令
                        self._process_prompt_commands(result)
                        
                        # 根据复盘决策决定下一步
                        if "[功能完成，建议重启]" in result:
                            logger.info("✅ 复盘确认功能完全完成，建议重启")
                            self.feature_completed = True
                            self.restart_pending = True
                            execution_results = []  # 清空执行结果
                            self.execution_start_time = None  # 重置执行计时器
                            self.last_activity_time = None  # 重置活动计时器
                            memory_system.add_history_entry("feature_complete", "功能完全完成，建议重启以加载新代码")
                        elif "[继续执行]" in result:
                            logger.info("📋 复盘要求继续执行工作")
                            # 保留执行结果，继续工作
                            # 保留计时器，继续计时
                            self.switch_phase("execution")
                        else:
                            logger.info("⚠️ 复盘未提供明确决策，继续执行")
                            # 默认继续执行
                            self.switch_phase("execution")
                        
                        # 记录到历史
                        memory_system.add_history_entry(
                            "review_phase",
                            f"复盘阶段 {self.review_iteration}",
                            result[:200] if result else ""
                        )
                        
                    except IflowTimeoutError as e:
                        logger.error(f"复盘阶段超时错误: {e}")
                        memory_system.add_history_entry("error", f"复盘阶段超时: {e}")
                    except IflowProcessError as e:
                        logger.error(f"复盘阶段进程错误: {e}")
                        memory_system.add_history_entry("error", f"复盘阶段进程错误: {e}")
                    except IflowTokenExpiredError as e:
                        logger.error(f"❌ iflow 令牌过期: {e}")
                        memory_system.add_history_entry("error", f"令牌过期: {e}")
                        self.ai_loop_running = False
                        break
                    except IflowMemoryError as e:
                        logger.error(f"❌ iflow 内存错误: {e}")
                        memory_system.add_history_entry("error", f"内存错误: {e}")
                        self.ai_loop_running = False
                        break
                    except IflowError as e:
                        logger.error(f"复盘阶段 Iflow 错误: {e}")
                        memory_system.add_history_entry("error", f"复盘阶段错误: {e}")
                    except Exception as e:
                        logger.error(f"复盘阶段未知错误: {e}", exc_info=True)
                        memory_system.add_history_entry("error", f"复盘阶段未知错误: {e}")
                
                # 检查代码变化
                if self._check_code_changes():
                    logger.info("🔄 检测到代码变化，准备重载 AI 循环...")
                    await self._restart_ai_loop_on_code_change()
                    break
                
                # 等待下一次迭代
                await asyncio.sleep(self.ai_loop_interval)
                
                # 定期保存记忆（每10次迭代）
                if self.ai_loop_iteration % 10 == 0:
                    memory_system.save_context(memory)
                    logger.info("记忆已保存")
                
        except asyncio.CancelledError:
            logger.info("AI 循环接收到停止信号")
        except Exception as e:
            logger.error(f"AI 循环错误: {e}", exc_info=True)
        finally:
            logger.info("AI 循环停止")
            self.ai_loop_running = False
            
            # 保存记忆和记录停止事件
            try:
                memory_system.save_context(memory)
                memory_system.add_history_entry("ai_loop_stop", "AI 循环停止")
                logger.info("记忆已保存")
            except Exception as e:
                logger.error(f"保存记忆失败: {e}")
            
            self.iflow.stop()
    async def start_ai_loop(self) -> None:
        """启动 AI 循环（外部调用接口）"""
        if self.ai_loop_running:
            logger.warning("AI 循环已在运行")
            return
        
        logger.info("启动 AI 循环进程...")
        self.ai_loop_task = asyncio.create_task(self.run_ai_loop())
    
    async def stop_ai_loop(self) -> None:
        """停止 AI 循环（外部调用接口）"""
        if not self.ai_loop_running:
            logger.warning("AI 循环未在运行")
            return
        
        logger.info("停止 AI 循环进程...")
        self.ai_loop_running = False
        
        if self.ai_loop_task:
            self.ai_loop_task.cancel()
            try:
                await self.ai_loop_task
            except asyncio.CancelledError:
                pass
            self.ai_loop_task = None
    
    def get_ai_loop_status(self) -> dict:
        """获取 AI 循环状态"""
        return {
            "running": self.ai_loop_running,
            "iteration": self.ai_loop_iteration,
            "interval": self.ai_loop_interval,
            "task_id": id(self.ai_loop_task) if self.ai_loop_task else None
        }
    
    def stop(self) -> None:
        """停止守护"""
        self.running = False
        logger.info("守护系统停止信号已发送")
    
    def try_auto_fix(self, error_context: Optional[str] = None, timeout: int = 300) -> bool:
        """尝试 AI 智能修复错误
        
        Args:
            error_context: 错误上下文信息
            timeout: AI 修复超时时间（秒），默认 300 秒（5 分钟）
        
        Returns:
            bool: 修复成功返回 True，否则返回 False
        """
        try:
            # 导入 IflowCaller
            from dev_bot.iflow import IflowCaller
            
            if self.iflow is None:
                # 设置超时参数
                self.iflow = IflowCaller(timeout=timeout)
            
            # 如果没有提供错误上下文，尝试从日志读取
            if not error_context:
                error_context = self._get_error_context()
            
            if not error_context:
                logger.warning("无法获取错误上下文，跳过 AI 修复")
                return False
            
            # 构建 AI 提示
            prompt = f"""Dev-Bot 崩溃了，请分析错误并提供修复方案。

错误信息：
{error_context}

请执行以下步骤：
1. 分析错误原因
2. 识别需要修改的文件
3. 提供具体的修复代码
4. 如果可以修复，直接使用文件操作工具修复问题

重要：
- 只修复代码错误，不要修改其他内容
- 保持代码风格一致
- 修复后返回 "FIXED: [修复描述]"
- 如果无法修复，返回 "CANNOT_FIX: [原因]"
- 修复操作应在 {timeout} 秒内完成

请开始修复。"""
            
            logger.info(f"🤖 AI 正在分析错误（超时: {timeout} 秒）...")
            
            # 调用 AI 分析（使用 asyncio.run 来运行异步调用）
            result = asyncio.run(self.iflow.call(prompt))
            logger.info(f"AI 分析结果: {result[:200]}...")
            
            # 检查是否修复成功
            if "FIXED:" in result or "修复成功" in result or "已修复" in result:
                logger.info("✅ AI 修复成功")
                self.code_modified = True
                self.last_modification_time = datetime.now()
                # 记录到历史
                from dev_bot import get_memory_system
                memory_system = get_memory_system()
                memory_system.add_history_entry("code_fix", "AI 修复成功，代码已修改")
                return True
            else:
                logger.warning("⚠️ AI 未能修复错误")
                return False
            
        except asyncio.TimeoutError:
            logger.error(f"AI 修复超时（{timeout} 秒）")
            return False
        except Exception as e:
            logger.error(f"AI 修复失败: {e}", exc_info=True)
            return False
    
    def _get_error_context(self) -> str:
        """获取错误上下文"""
        try:
            # 读取 supervisor.log 的最后 50 行
            supervisor_log = Path("supervisor.log")
            if supervisor_log.exists():
                with open(supervisor_log, 'r') as f:
                    lines = f.readlines()
                    return ''.join(lines[-50:])
            
            # 尝试读取 dev-bot.log
            dev_bot_log = Path("dev-bot.log")
            if dev_bot_log.exists():
                with open(dev_bot_log, 'r') as f:
                    lines = f.readlines()
                    return ''.join(lines[-50:])
            
            return ""
            
        except Exception as e:
            logger.error(f"读取错误日志失败: {e}")
            return ""
    
    async def monitor_file_changes(self, file_path: str) -> None:
        """监控文件变化"""
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return
        
        logger.info(f"监控文件变化: {file_path}")
        last_mtime = path.stat().st_mtime
        
        try:
            while self.running:
                current_mtime = path.stat().st_mtime
                if current_mtime != last_mtime:
                    logger.info(f"文件已更新: {file_path}")
                    last_mtime = current_mtime
                
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("文件监控已停止")
        except Exception as e:
            logger.error(f"文件监控失败: {e}")




    def initialize_prompt_template(self) -> None:
        """初始化基础提示词模板"""
        project_path = Path.cwd()
        
        self.base_prompt_template = f"""你是 Dev-Bot，一个 AI 驱动的自主开发代理。

## 项目信息
- 项目路径: {project_path}
- 技术栈: Python 3.9+, asyncio
- 代码风格: PEP 8, 4空格缩进

## 你的使命
分析当前项目 → 做出决策 → 执行开发 → 验证结果 → 继续改进

## 工作原则
1. 先分析，后行动 - 每次修改前先阅读相关代码
2. 小步快跑，频繁验证 - 每次只修改一个功能点
3. 遇到错误立即停止 - 分析错误原因，不要盲目重试
4. 修改代码后必须测试 - 使用 pytest 运行相关测试
5. 代码审查 - 修改后检查是否引入新问题

## 输出格式
每次输出必须包含：
- [分析] 当前状态、问题分析、相关文件
- [决策] 计划做什么、为什么这样做
- [执行] 具体操作步骤、修改的文件和行号
- [验证] 测试方法、测试结果
- [结论] 成功/失败、影响范围、下一步计划

## 停止条件
当以下情况时停止：
- 所有功能已实现且测试通过
- 连续3次遇到相同错误无法解决
- 需要用户决策或输入
- 接收到停止信号

## 安全规则
- 不要删除重要文件（如 .git/、venv/ 等）
- 不要提交未经测试的代码
- 不要修改配置文件（除非明确需要且有备份）
- 不要运行危险的系统命令
- 修改代码前先备份或使用 git commit

## 错误处理
- 遇到错误时，先阅读错误信息，分析原因
- 检查相关代码和测试用例
- 如果错误持续出现，记录错误并暂停
- 不要无限重试相同的操作

## 动态提示词功能
你可以通过以下方式优化自己的工作流程：
- 使用 [UPDATE_PROMPT: 新的提示词内容] 指令来修改提示词
- 使用 [RESTORE_PROMPT: 版本号] 指令来恢复历史版本的提示词
- 使用 [PROMPT_VERSION] 查看当前提示词版本
- 提示词修改会在下一轮迭代中生效

现在开始分析当前项目！

{{memory_summary}}

{{dynamic_instructions}}
"""

    def build_prompt(self, memory_summary: str = "", dynamic_instructions: str = "") -> str:
        """构建完整的提示词
        
        Args:
            memory_summary: 记忆摘要
            dynamic_instructions: 动态指令（来自 AI 的自我优化建议）
        
        Returns:
            完整的提示词
        """
        if self.base_prompt_template is None:
            self.initialize_prompt_template()
        
        # 使用当前提示词或基础模板
        template = self.current_prompt if self.current_prompt else self.base_prompt_template
        
        # 替换占位符
        prompt = template.replace("{memory_summary}", memory_summary)
        prompt = prompt.replace("{dynamic_instructions}", dynamic_instructions)
        
        return prompt
    def build_execution_prompt(self, memory_summary: str = "") -> str:
        """构建执行阶段提示词
        
        Args:
            memory_summary: 记忆摘要
        
        Returns:
            执行阶段提示词
        """
        phase_context = f"""
## 工作任务
分析项目状态，识别需要完成的工作，立即执行并完成所有相关工作。

## 执行要求（重要）
1. **立即执行**：不要只做分析和规划，必须实际执行工作
2. **使用工具**：使用可用的工具（read_file, write_file, replace, run_shell_command等）实际修改代码
3. **分步骤执行**：按照执行计划逐步完成每个步骤
4. **记录实际操作**：记录每个步骤的具体操作和实际结果
5. **验证结果**：每次修改后都要验证是否成功
6. **测试代码**：修改代码后运行测试确保没有问题
7. **完成评估**：0-100% 评估工作完成程度
8. **进入复盘**：完成后输出 [进入复盘]

## 输出格式（必须包含实际执行步骤）
工作目标：...
执行计划：...
执行过程：
- 步骤1：读取文件 XXX
  操作：实际读取了文件内容
  结果：...
- 步骤2：修改文件 XXX
  操作：使用 replace/write_file 修改了代码
  结果：修改成功/失败，原因：...
- 步骤3：运行测试
  操作：运行 pytest 命令
  结果：测试通过/失败，详细信息：...
执行结果：...
完成度：X%
测试验证：...
结论：[进入复盘]

## 重要提示
- **必须实际执行工作**，不能只做分析和规划
- 使用工具（read_file, write_file, replace, run_shell_command）实际修改代码
- 每个步骤都要记录具体的操作和结果
- 修改代码后必须运行测试验证
- 不要输出 [工作完成] 或 [继续执行]，只输出 [进入复盘]
"""
        
        return self.build_prompt(memory_summary, phase_context)
    
    def build_review_prompt(self, memory_summary: str = "", execution_results: str = "") -> str:
        """构建复盘阶段提示词
        
        Args:
            memory_summary: 记忆摘要
            execution_results: 执行阶段的结果
        
        Returns:
            复盘阶段提示词
        """
        phase_context = f"""
## 复盘任务
评估执行阶段的工作，判断功能是否完全开发完成且经过充分验证，并决定下一步行动。

## 重要说明
- **当前在同一个 iflow 会话中**，你可以访问之前的执行结果
- **根据复盘结果决定是否继续工作或完成功能**
- **如果需要继续执行，输出 [继续执行]；如果功能完全完成，输出 [功能完成，建议重启]**

## 评估维度
1. 工作完成度：0-100%，功能是否完全实现
2. 工作质量：代码规范、逻辑正确性
3. 测试验证：所有测试是否通过，功能是否稳定
4. 问题发现：是否有遗留问题或潜在风险
5. 功能完整性：功能是否可以独立运行和使用

## 决策标准
- 功能完全完成（完成度 >= 90% 且所有测试通过且无重大问题）：输出 [功能完成，建议重启]
- 继续开发（完成度 < 90% 或存在测试失败或重大问题）：输出 [继续执行]

## 输出格式
工作完成度：X%
质量评估：...
测试结果：...
问题分析：...
改进建议：...
决策结论：[功能完成，建议重启] 或 [继续执行]
后续计划：...

## 重要提示
- 只有在功能完全开发完成、所有测试通过、确认无问题后才输出 [功能完成，建议重启]
- 重启是为了加载新的代码和配置，确保最新功能生效
- 如果功能还有问题或未完成，继续执行直到功能完全稳定
"""
        
        return self.build_prompt(memory_summary, phase_context)
    
    def switch_phase(self, new_phase: str) -> None:
        """切换阶段
        
        Args:
            new_phase: 新阶段 (execution/review)
        """
        old_phase = self.current_phase
        self.current_phase = new_phase
        
        if new_phase == "review":
            # 进入复盘阶段，重置执行迭代
            logger.info(f"📊 执行阶段统计: {self.execution_iteration} 次迭代")
            self.execution_iteration = 0
            self.review_iteration += 1
            # 重置执行状态
            self.execution_state = {
                "current_task": None,
                "task_steps": [],
                "completed_steps": [],
                "total_tasks": 0,
                "completed_tasks": 0,
                "work_summary": ""
            }
        elif new_phase == "execution":
            # 进入执行阶段
            self.review_iteration = 0
            self.total_cycles += 1
            # execution_start_time 在循环中首次进入执行阶段时设置
        
        logger.info(f"🔄 阶段切换: {old_phase} -> {new_phase}")
        logger.info(f"📊 总循环数: {self.total_cycles}")

    
    def update_prompt(self, new_prompt: str, reason: str = "") -> bool:
        """更新提示词
        
        Args:
            new_prompt: 新的提示词内容
            reason: 修改原因
        
        Returns:
            是否成功更新
        """
        if not self.enable_dynamic_prompt:
            logger.warning("动态提示词功能已禁用")
            return False
        
        try:
            # 保存当前提示词到历史
            if self.current_prompt:
                self.prompt_history.append({
                    "version": self.prompt_version,
                    "prompt": self.current_prompt,
                    "timestamp": datetime.now().isoformat(),
                    "reason": f"版本 {self.prompt_version}"
                })
            
            # 更新提示词
            old_prompt = self.current_prompt
            self.current_prompt = new_prompt
            self.prompt_version += 1
            
            logger.info(f"🔄 提示词已更新: 版本 {self.prompt_version - 1} -> {self.prompt_version}")
            if reason:
                logger.info(f"📝 修改原因: {reason}")
            
            # 持久化到文件
            self._save_prompt_to_file()
            
            # 记录到历史
            from dev_bot import get_memory_system
            memory_system = get_memory_system()
            memory_system.add_history_entry(
                "prompt_update",
                f"提示词更新到版本 {self.prompt_version}",
                reason[:200] if reason else "AI 自我优化"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"❌ 更新提示词失败: {e}")
            return False
    
    def _save_prompt_to_file(self) -> None:
        """持久化提示词到文件"""
        try:
            prompt_data = {
                "version": self.prompt_version,
                "prompt": self.current_prompt,
                "base_template": self.base_prompt_template,
                "history": self.prompt_history,
                "last_updated": datetime.now().isoformat()
            }
            
            prompt_file = Path(".dev-bot-evolution") / "current_prompt.json"
            prompt_file.parent.mkdir(exist_ok=True)
            
            with open(prompt_file, 'w', encoding='utf-8') as f:
                json.dump(prompt_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 提示词已持久化到: {prompt_file}")
            
        except Exception as e:
            logger.error(f"❌ 持久化提示词失败: {e}")
    
    def restore_prompt(self, version: int) -> bool:
        """恢复历史版本的提示词
        
        Args:
            version: 要恢复的版本号
        
        Returns:
            是否成功恢复
        """
        try:
            # 查找指定版本
            for history_item in reversed(self.prompt_history):
                if history_item["version"] == version:
                    # 保存当前版本
                    current_version = self.prompt_version
                    self.prompt_history.append({
                        "version": current_version,
                        "prompt": self.current_prompt,
                        "timestamp": datetime.now().isoformat(),
                        "reason": f"恢复前版本 {current_version}"
                    })
                    
                    # 恢复指定版本
                    self.current_prompt = history_item["prompt"]
                    self.prompt_version = history_item["version"]
                    
                    logger.info(f"🔄 已恢复提示词版本: {version}")
                    return True
            
            logger.warning(f"未找到版本 {version} 的提示词")
            return False
        
        except Exception as e:
            logger.error(f"❌ 恢复提示词失败: {e}")
            return False
    
    def get_prompt_info(self) -> dict:
        """获取当前提示词信息
        
        Returns:
            提示词信息字典
        """
        return {
            "version": self.prompt_version,
            "dynamic_enabled": self.enable_dynamic_prompt,
            "history_count": len(self.prompt_history),
            "current_length": len(self.current_prompt) if self.current_prompt else 0,
            "template_length": len(self.base_prompt_template) if self.base_prompt_template else 0
        }
    def _scan_code_files(self) -> Dict[str, float]:
        """扫描代码文件并获取修改时间
        
        Returns:
            Dict[str, float]: 文件路径到修改时间的映射
        """
        code_files = {}
        try:
            # 扫描 dev_bot 目录下的所有 Python 文件
            dev_bot_dir = Path("dev_bot")
            if dev_bot_dir.exists():
                for py_file in dev_bot_dir.rglob("*.py"):
                    # 跳过 __pycache__ 目录
                    if "__pycache__" not in str(py_file):
                        mtime = py_file.stat().st_mtime
                        code_files[str(py_file)] = mtime
        except Exception as e:
            logger.error(f"扫描代码文件失败: {e}")
        
        return code_files
    
    def _check_code_changes(self) -> bool:
        """检查代码文件是否有变化
        
        Returns:
            bool: 如果有变化返回 True，否则返回 False
        """
        if not self.enable_code_reload:
            return False
        
        try:
            current_files = self._scan_code_files()
            
            # 如果是第一次扫描，初始化记录
            if not self.code_files_mtimes:
                self.code_files_mtimes = current_files
                return False
            
            # 检查文件变化
            changes = []
            for file_path, mtime in current_files.items():
                if file_path in self.code_files_mtimes:
                    if mtime != self.code_files_mtimes[file_path]:
                        changes.append(file_path)
                        logger.info(f"📝 检测到代码文件变化: {file_path}")
                else:
                    changes.append(file_path)
                    logger.info(f"📝 检测到新代码文件: {file_path}")
            
            # 更新记录
            self.code_files_mtimes = current_files
            
            if changes:
                logger.info(f"🔄 检测到 {len(changes)} 个代码文件变化")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"检查代码变化失败: {e}")
            return False
    
    async def _restart_ai_loop_on_code_change(self) -> None:
        """在代码变化时重启 AI 循环"""
        if not self.enable_code_reload:
            return
        
        if self.code_reload_pending:
            logger.info("⏳ 代码重载已在进行中，跳过")
            return
        
        self.code_reload_pending = True
        self.code_reload_count += 1
        
        logger.info("=" * 50)
        logger.info(f"🔄 触发代码热重载 (第 {self.code_reload_count} 次)")
        logger.info("=" * 50)
        
        try:
            # 记录重载事件
            from dev_bot import get_memory_system
            memory_system = get_memory_system()
            memory_system.add_history_entry(
                "code_reload",
                f"代码热重载 #{self.code_reload_count}",
                f"检测到代码变化，重启 AI 循环"
            )
            
            # 如果 AI 循环正在运行，先停止
            if self.ai_loop_running:
                logger.info("⏹️  停止当前 AI 循环...")
                await self.stop_ai_loop()
                
                # 等待一下确保完全停止
                await asyncio.sleep(1)
            
            # 重新启动 AI 循环
            logger.info("▶️  重新启动 AI 循环...")
            await self.start_ai_loop()
            
            logger.info(f"✅ 代码热重载完成 (第 {self.code_reload_count} 次)")
        
        except Exception as e:
            logger.error(f"❌ 代码热重载失败: {e}", exc_info=True)
        
        finally:
            self.code_reload_pending = False

    def _process_prompt_commands(self, ai_output: str) -> None:
        """处理 AI 输出中的提示词指令
        
        Args:
            ai_output: AI 的输出文本
        """
        if not self.enable_dynamic_prompt:
            return
        
        # 检测 UPDATE_PROMPT 指令
        if "[UPDATE_PROMPT:" in ai_output:
            try:
                # 提取新的提示词内容
                start = ai_output.find("[UPDATE_PROMPT:")
                end = ai_output.find("]", start)
                if start != -1 and end != -1:
                    new_prompt = ai_output[start + 14:end].strip()
                    # 提取原因（如果有）
                    reason_match = re.search(r"原因[：:](.+?)(?:\n|$)", new_prompt)
                    reason = reason_match.group(1).strip() if reason_match else "AI 自我优化"
                    
                    # 分离提示词内容和原因
                    prompt_content = new_prompt
                    if "原因：" in prompt_content or "原因:" in prompt_content:
                        prompt_content = re.sub(r"原因[：:].+$", "", prompt_content, flags=re.MULTILINE).strip()
                    
                    # 更新提示词
                    if self.update_prompt(prompt_content, reason):
                        logger.info(f"✅ AI 已通过指令更新提示词（版本 {self.prompt_version}）")
            except Exception as e:
                logger.error(f"❌ 处理 UPDATE_PROMPT 指令失败: {e}")
        
        # 检测 RESTORE_PROMPT 指令
        if "[RESTORE_PROMPT:" in ai_output:
            try:
                # 提取版本号
                start = ai_output.find("[RESTORE_PROMPT:")
                end = ai_output.find("]", start)
                if start != -1 and end != -1:
                    version_str = ai_output[start + 16:end].strip()
                    try:
                        version = int(version_str)
                        if self.restore_prompt(version):
                            logger.info(f"✅ AI 已通过指令恢复提示词到版本 {version}")
                    except ValueError:
                        logger.warning(f"无效的版本号: {version_str}")
            except Exception as e:
                logger.error(f"❌ 处理 RESTORE_PROMPT 指令失败: {e}")
        
        # 检测 PROMPT_VERSION 查询
        if "[PROMPT_VERSION]" in ai_output:
            prompt_info = self.get_prompt_info()
            logger.info(f"📋 当前提示词版本信息: 版本 {prompt_info['version']}, 历史记录 {prompt_info['history_count']} 条")
async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dev-Bot 守护系统")
    parser.add_argument(
        "--pid",
        type=int,
        help="要监控的进程 PID (默认: 自身)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="健康检查间隔秒数 (默认: 30)"
    )
    
    args = parser.parse_args()
    
    # 创建守护
    guardian = Guardian(check_interval=args.interval)
    
    # 启动守护
    try:
        await guardian.start(args.pid)
    except KeyboardInterrupt:
        logger.info("\n接收到中断信号")
    finally:
        guardian.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)