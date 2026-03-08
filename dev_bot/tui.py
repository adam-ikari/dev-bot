#!/usr/bin/env python3
"""Dev-Bot TUI 界面 - 简洁的终端用户界面"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Footer,
    Header,
    Input,
    RichLog,
    Static,
    TextArea,
)
from textual.reactive import reactive

from dev_bot import AIRunner, get_memory_system
from dev_bot.iflow import IflowCaller, IflowError, IflowTokenExpiredError, IflowMemoryError

# 配置日志
logging.basicConfig(level=logging.INFO)


class StatusBar(Static):
    """状态栏 - 显示运行状态和消息"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.status = "stopped"
        self.iteration_count = 0
        self.start_time = datetime.now()
        self.message = "就绪"
    
    def set_status(self, status: str):
        """设置状态"""
        self.status = status
        self.update_display()
    
    def set_iteration(self, count: int):
        """设置迭代次数"""
        self.iteration_count = count
        self.update_display()
    
    def set_message(self, message: str):
        """设置消息"""
        self.message = message
        self.update_display()
    
    def update_display(self):
        """更新显示"""
        status_emoji = {
            "running": "🟢",
            "paused": "🟡",
            "stopped": "🔴"
        }.get(self.status, "⚪")
        
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split(".")[0]
        
        self.update(
            f"🤖 Dev-Bot v2.0    [{status_emoji} {self.status.upper()}] "
            f"迭代: {self.iteration_count}    ⏱️ {elapsed_str}    "
            f"💬 {self.message}"
        )


class LogView(RichLog):
    """日志视图 - 显示 AI 运行日志"""

    def __init__(self, **kwargs):
        super().__init__(
            max_lines=1000,
            wrap=True,
            highlight=True,
            **kwargs
        )


class REPLView(Vertical):
    """REPL 视图 - 用户输入"""

    def __init__(self, on_submit, **kwargs):
        super().__init__(**kwargs)
        self.on_submit = on_submit
        self.input_history = []
        self.history_index = -1
        self._min_height = 3
        self._max_height = 10
    
    def compose(self) -> ComposeResult:
        yield Static("💬 用户输入 (按 Enter 发送):", classes="label")
        from textual.widgets import TextArea
        yield TextArea("", placeholder="输入指令...", id="repl-input")
    
    def on_mount(self) -> None:
        text_area = self.query_one("#repl-input", TextArea)
        text_area.show_line_numbers = False
        text_area.soft_wrap = True
    
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """根据内容调整高度"""
        text_area = event.text_area
        line_count = len(text_area.text.split('\n'))
        
        # 计算自适应高度
        new_height = max(self._min_height, min(line_count, self._max_height))
        
        # 更新容器高度
        self.styles.height = new_height
    
    def on_key(self, event) -> None:
        """处理键盘事件"""
        text_area = self.query_one("#repl-input", TextArea)
        
        # Enter 键提交（单行模式）
        if event.key == "enter" and not event.shift:
            event.prevent_default()
            if text_area.text.strip():
                self.input_history.append(text_area.text)
                self.history_index = -1
                self.on_submit(text_area.text)
                text_area.text = ""
                # 重置高度
                self.styles.height = self._min_height
        # Ctrl+Enter 在多行输入时换行
        elif event.key == "enter" and event.shift:
            event.prevent_default()
            # 允许默认行为（换行）
            pass
        # 上箭头 - 历史记录
        elif event.key == "up":
            if self.input_history and self.history_index < len(self.input_history) - 1:
                self.history_index += 1
                text_area.text = self.input_history[-(self.history_index + 1)]
        # 下箭头 - 历史记录
        elif event.key == "down":
            if self.history_index > 0:
                self.history_index -= 1
                text_area.text = self.input_history[-(self.history_index + 1)]
            elif self.history_index == 0:
                self.history_index = -1
                text_area.text = ""


class DevBotTUI(App):
    """Dev-Bot TUI 主应用"""

    CSS = """
    Screen {
        layout: vertical;
    }

    #status-bar {
        dock: top;
        padding: 0 1;
        background: $primary;
        color: $text;
        text-style: bold;
        height: 1;
    }

    #main-container {
        height: 1fr;
    }

    #log-view {
        height: 1fr;
        min-height: 10;
        border: solid green;
    }

    REPLView {
        height: auto;
        min-height: 3;
        max-height: 15;
        border: solid yellow;
    }

    TextArea {
        height: auto;
        min-height: 2;
        max-height: 10;
    }

    .label {
        text-style: bold;
        height: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "退出"),
        ("space", "toggle_pause", "暂停/继续"),
        ("c", "clear_log", "清空日志"),
        ("h", "show_help", "帮助"),
        ("ctrl+c", "quit", "退出"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 检查 iflow 可用性
        self.iflow_available, self.iflow_status = IflowCaller.check_availability()
        
        # 初始化 iflow 对象
        self.iflow = IflowCaller() if self.iflow_available else None
        self.ai_runner = AIRunner() if self.iflow_available else None
        self.memory_system = get_memory_system()
        
        # 重定向日志到TUI log_view
        self._setup_logging_to_tui()
        self.memory = self.memory_system.load_context()
        self.iteration_count = 0
        self.ai_iteration_count = 0
        self.is_paused = False
        self.ai_loop_stopped = False
        self.start_time = datetime.now()

    def compose(self) -> ComposeResult:
        yield StatusBar(id="status-bar")
        yield Container(
            LogView(id="log-view"),
            REPLView(on_submit=self._handle_repl_input),
            id="main-container"
        )
        yield Footer()

    def _setup_logging_to_tui(self) -> None:
        """设置日志输出到TUI log_view"""
        
        class TUILogHandler(logging.Handler):
            """自定义日志处理器，将日志输出到TUI log_view"""
            
            def __init__(self, app):
                super().__init__()
                self.app = app
            
            def emit(self, record):
                try:
                    if not hasattr(self.app, "_components_mounted"):
                        return
                    
                    log_view = self.app.query_one("#log-view", RichLog)
                    if log_view is None:
                        return
                    
                    msg = record.getMessage()
                    
                    if record.levelno >= logging.ERROR:
                        log_view.write(f"[red]ERROR: {msg}[/red]")
                    elif record.levelno >= logging.WARNING:
                        log_view.write(f"[yellow]WARNING: {msg}[/yellow]")
                    elif record.levelno >= logging.INFO:
                        log_view.write(f"[green]INFO: {msg}[/green]")
                    else:
                        log_view.write(f"[dim]DEBUG: {msg}[/dim]")
                except Exception:
                    pass
        
        root_logger = logging.getLogger()
        tui_handler = TUILogHandler(self)
        tui_handler.setLevel(logging.INFO)
        root_logger.addHandler(tui_handler)
        root_logger.setLevel(logging.INFO)
    
    def on_mount(self) -> None:
        log_view = self.query_one("#log-view", RichLog)
        status_bar = self.query_one("#status-bar", StatusBar)
        
        self._components_mounted = True
        status_bar.start_time = self.start_time
        status_bar.set_status("running")
        status_bar.set_message("AI 正在自主工作")

        log_view.write("[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]")
        log_view.write("[bold cyan]║  🤖 Dev-Bot v2.0 - AI 驱动的自主开发工具                        ║[/bold cyan]")
        log_view.write("[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]")
        log_view.write("")
        
        if self.iflow_available:
            log_view.write(f"[green]✅ iflow 可用: {self.iflow_status}[/green]")
        else:
            log_view.write(f"[red]❌ iflow 不可用: {self.iflow_status}[/red]")
            log_view.write("[yellow]⚠️  AI 功能将不可用，请先安装并配置 iflow[/yellow]")
            self.ai_loop_stopped = True
            status_bar.set_status("stopped")
            status_bar.set_message("iflow 不可用")
        
        log_view.write("")
        log_view.write("[dim]按 [h] 查看帮助，按 [q] 退出[/dim]")
        log_view.write("")

        # 启动 AI 自动分析任务
        self.set_interval(1, self._auto_ai_loop)

    async def _handle_repl_input(self, prompt: str) -> None:
        """处理 REPL 输入"""
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(f"[bold cyan]> 用户指令: {prompt}[/bold cyan]")

        self.memory_system.add_history_entry("user_input", prompt)

        if prompt.strip().lower() == "restart":
            if self.ai_loop_stopped:
                self.ai_loop_stopped = False
                self.is_paused = False
                status_bar = self.query_one("#status-bar", StatusBar)
                status_bar.set_status("running")
                status_bar.set_message("AI 正在自主工作")
                log_view.write("[green]✓ AI 循环已重新启动[/green]")
                self.memory_system.add_history_entry("info", "AI 循环重新启动")
            else:
                log_view.write("[dim]AI 循环正在运行，无需重新启动[/dim]")
            return

        if not self.iflow_available or self.iflow is None:
            log_view.write("[red]❌ iflow 不可用，无法处理用户指令[/red]")
            log_view.write(f"[red]状态: {self.iflow_status}[/red]")
            return

        try:
            result = await self.iflow.call(prompt)
            log_view.write(result)
            self.memory_system.add_history_entry("ai_output", result[:200])
        except IflowTokenExpiredError as e:
            log_view.write(f"[red]❌ iflow 令牌过期[/red]")
            log_view.write("[yellow]请执行以下命令重新授权:[/yellow]")
            log_view.write("[bold cyan]  iflow auth[/bold cyan]")
            
            self.is_paused = True
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_status("paused")
            status_bar.set_message("令牌过期，需要重新授权")
            
            self.memory_system.add_history_entry("error", f"令牌过期: {e}")
        except IflowMemoryError as e:
            log_view.write("[red]内存不足: iflow 进程内存不足[/red]")
            log_view.write("建议: 关闭其他应用、增加系统内存")
            log_view.write("修复后输入: restart")
            
            self.ai_loop_stopped = True
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_status("stopped")
            status_bar.set_message("内存不足")
            
            self.memory_system.add_history_entry("error", f"内存错误: {e}")
        except IflowError as e:
            log_view.write(f"[red]错误: {e}[/red]")
            self.memory_system.add_history_entry("error", str(e))
    
    async def _auto_ai_loop(self) -> None:
        """自动 AI 循环"""
        if self.is_paused or self.ai_loop_stopped:
            return

        self.ai_iteration_count += 1
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(f"[yellow]🔄 AI 分析 #{self.ai_iteration_count}[/yellow]")

        project_path = Path.cwd()
        memory_summary = self.memory_system.get_context_summary()

        prompt = f"""你是 Dev-Bot，一个 AI 驱动的自主开发代理。

## 项目信息
- 项目路径: {project_path}
- 当前迭代: #{self.ai_iteration_count}

## 当前状态
{memory_summary}

## 工作原则
1. 先分析，后行动 - 每次修改前先阅读相关代码
2. 小步快跑，频繁验证 - 每次只修改一个功能点
3. 遇到错误立即停止 - 分析错误原因，不要盲目重试
4. 修改代码后必须测试 - 使用 pytest 运行相关测试
5. 完全自主工作 - 不需要用户干预，自己决策、自己执行

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

现在开始自主分析和工作！
"""

        if not self.iflow_available or self.iflow is None:
            log_view.write("[red]❌ iflow 不可用，无法进行 AI 分析[/red]")
            log_view.write(f"[red]状态: {self.iflow_status}[/red]")
            self.ai_loop_stopped = True
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_status("stopped")
            status_bar.set_message("iflow 不可用")
            return

        try:
            result = await self.iflow.call(prompt)
            log_view.write(result)
            self.memory_system.add_history_entry("ai_analysis", result[:200])
            
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_iteration(self.ai_iteration_count)

        except IflowTokenExpiredError as e:
            log_view.write(f"[red]❌ iflow 令牌过期[/red]")
            log_view.write("[yellow]请执行以下命令重新授权:[/yellow]")
            log_view.write("[bold cyan]  iflow auth[/bold cyan]")
            
            self.is_paused = True
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_status("paused")
            status_bar.set_message("令牌过期，需要重新授权")
            
            self.memory_system.add_history_entry("error", f"令牌过期: {e}")
        except IflowMemoryError as e:
            log_view.write("[red]内存不足: iflow 进程内存不足[/red]")
            log_view.write("建议: 关闭其他应用、增加系统内存")
            log_view.write("修复后输入: restart")
            
            self.ai_loop_stopped = True
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_status("stopped")
            status_bar.set_message("内存不足")
            
            self.memory_system.add_history_entry("error", f"内存错误: {e}")
        except Exception as e:
            log_view.write(f"[red]AI 分析失败: {e}[/red]")
            self.memory_system.add_history_entry("error", str(e))

    def action_toggle_pause(self) -> None:
        """切换暂停状态"""
        self.is_paused = not self.is_paused

        status_bar = self.query_one("#status-bar", StatusBar)
        log_view = self.query_one("#log-view", RichLog)

        if self.is_paused:
            status_bar.set_status("paused")
            status_bar.set_message("已暂停")
            log_view.write("[yellow]⏸️ AI 已暂停[/yellow]")
        else:
            status_bar.set_status("running")
            status_bar.set_message("AI 正在自主工作")
            log_view.write("[green]▶️ AI 继续工作[/green]")

    def action_clear_log(self) -> None:
        """清空日志"""
        log_view = self.query_one("#log-view", RichLog)
        log_view.clear()
        log_view.write("[dim]日志已清空[/dim]")

    def action_show_help(self) -> None:
        """显示帮助"""
        log_view = self.query_one("#log-view", RichLog)
        log_view.write("")
        log_view.write("[bold]帮助信息[/bold]")
        log_view.write("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log_view.write("[q] 或 [Ctrl+C] - 退出程序")
        log_view.write("[Space] - 暂停/继续 AI 运行")
        log_view.write("[c] - 清空日志")
        log_view.write("[h] - 显示此帮助信息")
        log_view.write("")
        log_view.write("输入指令:")
        log_view.write("  直接在右侧输入框输入指令，按 Enter 发送")
        log_view.write("  示例: '创建任务列表: 编写测试、优化性能'")
        log_view.write("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log_view.write("")

    def on_unmount(self) -> None:
        if self.iflow:
            self.iflow.stop()
        
        try:
            self.memory_system.save_context(self.memory)
        except Exception:
            pass


def main():
    """Dev-Bot TUI 主入口"""
    try:
        app = DevBotTUI()
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ TUI 启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()