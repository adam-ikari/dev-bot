#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dev-Bot TUI 界面 - 终端用户界面

提供响应式分割布局：
- 上方区域：AI 运行日志
- 下方区域：REPL 输入
- 支持手动调整分隔位置
- 自动响应终端大小变化
"""

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Footer,
    Header,
    Input,
    Log,
    RichLog,
    Static,
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


class REPLView(Container):
    """REPL 视图 - 用户输入区域"""
    
    def __init__(self, on_submit, **kwargs):
        super().__init__(**kwargs)
        self.on_submit = on_submit
        self.input_history = []  # 输入历史
        self.history_index = -1  # 当前历史索引
        self.current_input = ""  # 当前输入（在浏览历史时保存）
        
    def compose(self) -> ComposeResult:
        """构建 REPL 组件"""
        yield Static("REPL 输入 (按 Enter 发送, ↑/↓ 滚动历史):", classes="repl-label")
        yield Input(placeholder="输入你的指令...", id="repl-input", classes="repl-input")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """处理输入提交"""
        if event.value.strip():
            # 保存到历史
            self.input_history.append(event.value)
            self.history_index = -1
            self.current_input = ""
            
            # 调用回调
            self.on_submit(event.value)
            event.input.value = ""
    
    def on_key(self, event) -> None:
        """处理按键事件"""
        input_widget = self.query_one("#repl-input", Input)
        
        # 只在输入框有焦点时处理上下键
        if input_widget.has_focus:
            if event.key == "up":
                self._navigate_history(-1)
            elif event.key == "down":
                self._navigate_history(1)
    
    def _navigate_history(self, direction: int) -> None:
        """导航历史输入"""
        if not self.input_history:
            return
        
        input_widget = self.query_one("#repl-input", Input)
        
        # 保存当前输入（如果是第一次按上下键）
        if self.history_index == -1 and direction == -1:
            self.current_input = input_widget.value
        
        # 更新索引
        new_index = self.history_index + direction
        
        if new_index < -len(self.input_history):
            # 已经到达最旧的历史，不再向前
            return
        elif new_index >= 0:
            # 超出最新历史，恢复当前输入
            input_widget.value = self.current_input
            self.history_index = -1
            self.current_input = ""
        else:
            # 显示历史输入
            self.history_index = new_index
            input_widget.value = self.input_history[self.history_index]
            # 将光标移动到末尾
            input_widget.cursor_position = len(input_widget.value)


class DevBotTUI(App):
    """Dev-Bot TUI 主应用"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #log-container {
        height: 1fr;
        border: solid green;
        border-subtitle: "AI 运行日志";
    }
    
    #repl-container {
        height: auto;
        border: solid blue;
        border-subtitle: "REPL 输入";
        min-height: 5;
    }
    
    .repl-label {
        padding: 0 1;
        color: bold;
    }
    
    .repl-input {
        margin: 1 0 0 0;
    }
    
    RichLog {
        scrollbar-size: 1 1;
    }
    """
    
    BINDINGS = [
        ("ctrl+c", "quit", "退出"),
        ("ctrl+q", "quit", "退出"),
        ("f1", "toggle_full_log", "全屏日志"),
        ("f2", "toggle_full_repl", "全屏 REPL"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_inputs = []
        self.user_input_callback = None
        self.full_screen_mode = None  # 全屏模式: 'log' | 'repl' | None
        
    def compose(self) -> ComposeResult:
        """构建 TUI 界面"""
        yield Header()
        yield Vertical(
            Container(
                LogView(id="log-view"),
                id="log-container"
            ),
            REPLView(
                on_submit=self._handle_repl_input,
                id="repl-container"
            ),
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """界面挂载时的初始化"""
        log_view = self.query_one("#log-view", RichLog)
        
        # 显示 ASCII Logo - 精美的 DEV-BOT
        logo = """
██╗  ██╗ █████╗ ███████╗██╗     ██╗███╗   ██╗ ██████╗ 
██║  ██║██╔══██╗██╔════╝██║     ██║████╗  ██║██╔═══██╗
███████║███████║███████╗██║     ██║██╔██╗ ██║██║   ██║
██╔══██║██╔══██║╚════██║██║     ██║██║╚██╗██║██║   ██║
██║  ██║██║  ██║███████║███████╗██║██║ ╚████║╚██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 
    ╔╗ ┬ ┬┌─┐┌─┐┌─┐┬┌┐┌┐┬  ┌─┐┌┬┐┌─┐  ╦ ╦┌─┐┌┐┌┌─┐
    ╠╩╗│ │├┤ │ ┬├─┤│││││└┐├─┤ ││├┤  ╠═╣├┤ │││└─┐
    ╚═╝└─┘└─┘└─┘┴ ┴┴┘└┘└─┘┴ ┴┴ ┴ ┴ ┴└─┘ ╩ ╩└─┘┘└┘└─┘
            AI 驱动的 Spec 开发系统
"""
        
        log_view.write(f"[bold cyan]{logo}[/bold cyan]")
        log_view.write("[bold green]TUI 模式已启动[/bold green]\n")
        log_view.write("[yellow]↑ 方向: AI 运行日志[/yellow]\n")
        log_view.write("[yellow]↓ 方向: REPL 输入[/yellow]\n")
        log_view.write("[dim]快捷键:[/dim]\n")
        log_view.write("[dim]  Ctrl+C/Q: 退出[/dim]\n")
        log_view.write("[dim]  F1: 全屏日志[/dim]\n")
        log_view.write("[dim]  F2: 全屏 REPL[/dim]\n")
        log_view.write("[dim]  ↑/↓: 滚动历史输入[/dim]\n")
        log_view.write("-" * 50 + "\n")
        
        # 应用初始布局
        self._update_layout()
    
    def on_resize(self, event) -> None:
        """屏幕大小变化时自动调整布局"""
        if not self.full_screen_mode:
            self._auto_adjust_repl_height()
    
    def _update_layout(self) -> None:
        """更新布局"""
        if self.full_screen_mode == 'log':
            # 全屏日志模式
            log_container = self.query_one("#log-container", Container)
            repl_container = self.query_one("#repl-container", Container)
            log_container.styles.height = "100%"
            repl_container.styles.height = "0"
            log_container.styles.display = "block"
            repl_container.styles.display = "none"
        elif self.full_screen_mode == 'repl':
            # 全屏 REPL 模式
            log_container = self.query_one("#log-container", Container)
            repl_container = self.query_one("#repl-container", Container)
            log_container.styles.height = "0"
            repl_container.styles.height = "100%"
            log_container.styles.display = "none"
            repl_container.styles.display = "block"
        else:
            # 正常分割模式
            self._auto_adjust_repl_height()
    
    def _auto_adjust_repl_height(self) -> None:
        """根据屏幕高度自动调整 REPL 高度"""
        screen_height = self.size.height
        
        # 计算合适的 REPL 高度
        # 最小 5 行，最大 15 行，默认根据屏幕高度动态调整
        if screen_height < 20:
            # 小屏幕：REPL 占 30%
            repl_height_percent = 30
        elif screen_height < 30:
            # 中等屏幕：REPL 占 25%
            repl_height_percent = 25
        else:
            # 大屏幕：REPL 占 20%
            repl_height_percent = 20
        
        # 确保 REPL 至少有 5 行
        min_repl_lines = 5
        min_repl_percent = (min_repl_lines / screen_height) * 100
        
        if repl_height_percent < min_repl_percent:
            repl_height_percent = min_repl_percent
        
        # 确保 REPL 不超过 40%
        if repl_height_percent > 40:
            repl_height_percent = 40
        
        # 应用布局
        log_container = self.query_one("#log-container", Container)
        repl_container = self.query_one("#repl-container", Container)
        
        log_container.styles.height = f"{100 - repl_height_percent}%"
        repl_container.styles.height = f"{repl_height_percent}%"
        log_container.styles.display = "block"
        repl_container.styles.display = "block"
    
    def action_toggle_full_log(self) -> None:
        """切换全屏日志模式"""
        if self.full_screen_mode == 'log':
            self.full_screen_mode = None
            self.log("[info]退出全屏日志模式")
        else:
            self.full_screen_mode = 'log'
            self.log("[info]进入全屏日志模式")
        self._update_layout()
    
    def action_toggle_full_repl(self) -> None:
        """切换全屏 REPL 模式"""
        if self.full_screen_mode == 'repl':
            self.full_screen_mode = None
            self.log("[info]退出全屏 REPL 模式")
        else:
            self.full_screen_mode = 'repl'
            self.log("[info]进入全屏 REPL 模式")
        self._update_layout()
    
    def _handle_repl_input(self, text: str) -> None:
        """处理 REPL 输入"""
        log_view = self.query_one("#log-view", RichLog)
        
        # 记录用户输入
        log_view.write(f"[bold green]用户:[/bold green] {text}")
        self.user_inputs.append(text)
        
        # 调用回调函数
        if self.user_input_callback:
            self.user_input_callback(text)
    
    def log(self, message: str, level: str = "info") -> None:
        """添加日志消息"""
        log_view = self.query_one("#log-view", RichLog)
        
        color_map = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "ai": "cyan",
            "debug": "dim",
        }
        
        color = color_map.get(level, "white")
        log_view.write(f"[{color}]{message}[/{color}]")
    
    def log_ai_output(self, output: str) -> None:
        """记录 AI 输出"""
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(
            f"\n[bold cyan]AI 输出:[/bold cyan]\n"
            f"[dim]{output}[/dim]\n"
        )
    
    def log_error(self, error: str) -> None:
        """记录错误"""
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(
            f"\n[bold red]错误:[/bold red]\n"
            f"{error}\n"
        )
    
    def log_success(self, message: str) -> None:
        """记录成功消息"""
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(f"[bold green]✓ {message}[/bold green]\n")
    
    def set_user_input_callback(self, callback):
        """设置用户输入回调函数"""
        self.user_input_callback = callback
    
    def get_user_inputs(self) -> list:
        """获取用户输入列表"""
        return self.user_inputs.copy()
    
    def clear_log(self) -> None:
        """清空日志"""
        log_view = self.query_one("#log-view", RichLog)
        log_view.clear()


class TUILogger:
    """TUI 日志记录器 - 用于与现有代码集成"""
    
    def __init__(self, tui_app: DevBotTUI):
        self.tui = tui_app
    
    def info(self, message: str) -> None:
        """记录信息"""
        self.tui.log(message, level="info")
    
    def success(self, message: str) -> None:
        """记录成功"""
        self.tui.log_success(message)
    
    def warning(self, message: str) -> None:
        """记录警告"""
        self.tui.log(message, level="warning")
    
    def error(self, message: str) -> None:
        """记录错误"""
        self.tui.log_error(message)
    
    def ai_output(self, output: str) -> None:
        """记录 AI 输出"""
        self.tui.log_ai_output(output)
    
    def debug(self, message: str) -> None:
        """记录调试信息"""
        self.tui.log(message, level="debug")


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    app = DevBotTUI()
    
    def handle_user_input(text: str):
        print(f"收到用户输入: {text}")
    
    app.set_user_input_callback(handle_user_input)
    
    # 模拟一些日志输出
    async def simulate_logs():
        import asyncio
        await asyncio.sleep(1)
        app.log("启动 Dev-Bot...")
        await asyncio.sleep(1)
        app.log("加载配置文件...")
        await asyncio.sleep(1)
        app.log_success("配置加载成功")
        await asyncio.sleep(1)
        app.log_ai_output("这是 AI 的输出内容...")
    
    import asyncio
    
    async def main():
        async with app.run_task():
            await simulate_logs()
    
    asyncio.run(main())
