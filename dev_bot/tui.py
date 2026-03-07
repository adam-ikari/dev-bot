#!/usr/bin/env python3
"""
Dev-Bot TUI 界面 - 终端用户界面

改进布局 + AI 可控制的展示组件：
- 顶部状态栏：显示运行状态、迭代次数、时间
- 左侧监控面板：CPU、内存、时间
- 右侧日志区：AI 运行日志
- 中间内容区：AI 可控制的展示组件（checklist、table、tree、card）
- 底部面板：Spec 问题 + REPL 输入
"""

import asyncio
import psutil
from datetime import datetime, timedelta
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import (
    Footer,
    Header,
    Input,
    RichLog,
    Static,
    ProgressBar,
    DataTable,
    Checkbox,
    Label,
)
from textual import events
from textual.reactive import reactive

from dev_bot import IflowCaller, IflowError, get_memory_system


class StatusBar(Static):
    """状态栏 - 显示运行状态、迭代次数、时间"""
    
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


class MonitorPanel(Static):
    """监控面板 - 显示 CPU、内存、时间"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_task = None
    
    def on_mount(self):
        """挂载时启动更新任务"""
        self.update_task = asyncio.create_task(self.update_loop())
    
    async def update_loop(self):
        """更新循环"""
        while True:
            self.update_display()
            await asyncio.sleep(2)
    
    def update_display(self):
        """更新显示"""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.Process().memory_info()
        memory_mb = memory.rss / 1024 / 1024
        
        elapsed = datetime.now() - self.app.start_time if hasattr(self.app, 'start_time') else timedelta()
        elapsed_str = str(elapsed).split(".")[0]
        
        content = f"""📊 监控
━━━━━━━━━━━━
CPU: {cpu_percent}%
{"█" * int(cpu_percent // 5)}{" " * (20 - int(cpu_percent // 5))}

内存: {memory_mb:.0f} MB / 2048 MB
{"█" * int((memory_mb / 2048) * 20)}

⏱️ 运行时间: {elapsed_str}"""
        
        self.update(content)


class ContentPanel(Container):
    """内容面板 - AI 可控制的展示组件区域"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_component = None
        self.components = {}
    
    def show_checklist(self, title: str, items: list):
        """显示检查清单"""
        self.clear()
        
        self.mount(Label(f"✅ {title}", classes="component-title"))
        
        for item in items:
            label = item.get("text", item)
            checked = item.get("checked", False)
            self.mount(Checkbox(label, value=checked, classes="checklist-item"))
        
        self.current_component = "checklist"
    
    def show_table(self, title: str, columns: list, rows: list):
        """显示表格"""
        self.clear()
        
        self.mount(Label(f"📊 {title}", classes="component-title"))
        
        table = DataTable()
        table.add_column(*columns)
        
        for row in rows:
            table.add_row(*row)
        
        self.mount(table)
        self.current_component = "table"
    
    def show_tree(self, title: str, items: list):
        """显示树形结构"""
        self.clear()
        
        self.mount(Label(f"🌳 {title}", classes="component-title"))
        
        for item in items:
            indent = "  " * item.get("level", 0)
            prefix = "├─" if item.get("has_children") else "└─"
            label = f"{indent}{prefix} {item.get('text', '')}"
            self.mount(Label(label, classes="tree-item"))
        
        self.current_component = "tree"
    
    def show_cards(self, title: str, cards: list):
        """显示卡片"""
        self.clear()
        
        self.mount(Label(f"📋 {title}", classes="component-title"))
        
        for card in cards:
            card_content = f"""
┌─────────────────────┐
│ {card.get('title', '')}
│ {card.get('description', '')}
└─────────────────────┘"""
            self.mount(Static(card_content, classes="card-item"))
        
        self.current_component = "cards"
    
    def show_metrics(self, title: str, metrics: list):
        """显示指标"""
        self.clear()
        
        self.mount(Label(f"📈 {title}", classes="component-title"))
        
        for metric in metrics:
            value = metric.get("value", 0)
            max_val = metric.get("max", 100)
            label = metric.get("label", "")
            percentage = min((value / max_val) * 100, 100)
            
            bar = "█" * int(percentage // 5)
            empty = " " * (20 - int(percentage // 5))
            
            content = f"{label}\n{bar}{empty} {value}/{max_val}"
            self.mount(Static(content, classes="metric-item"))
        
        self.current_component = "metrics"
    
    def clear(self):
        """清空面板"""
        self.children.clear()


class LogView(RichLog):
    """日志视图 - 显示 AI 运行日志"""

    def __init__(self, **kwargs):
        super().__init__(
            max_lines=1000,
            wrap=True,
            highlight=True,
            **kwargs
        )


class SpecQuestionView(Container):
    """Spec 问题视图"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.questions = []
    
    def update_questions(self, questions):
        """更新问题列表"""
        self.questions = questions
        self.update_view()
    
    def compose(self) -> ComposeResult:
        yield Static("📋 Spec 问题", classes="spec-label")
        yield Static("[dim]✓ 没有待处理的 Spec 问题[/dim]", id="spec-content", classes="spec-content")
    
    def update_view(self):
        try:
            content = self.query_one("#spec-content", Static)
            if not self.questions:
                content.update("[dim]✓ 没有待处理的 Spec 问题[/dim]")
            else:
                lines = []
                for i, q in enumerate(self.questions, 1):
                    lines.append(f"  [{i}] {q}")
                content.update("\n".join(lines))
        except Exception:
            pass


class REPLView(Container):
    """REPL 视图"""

    def __init__(self, on_submit, **kwargs):
        super().__init__(**kwargs)
        self.on_submit = on_submit
        self.input_history = []
        self.history_index = -1
    
    def compose(self) -> ComposeResult:
        yield Input(placeholder="输入你的指令 (Enter 发送, ↑/↓ 历史)...", id="repl-input")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            self.input_history.append(event.value)
            self.history_index = -1
            self.on_submit(event.value)
            event.input.value = ""


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
    }

    #main-container {
        height: 1fr;
    }

    #log-container {
        height: 1fr;
        border: solid green;
    }

    #monitor-panel {
        width: 20;
        border: solid blue;
        padding: 0 1;
    }

    #content-panel {
        width: 30;
        border: solid cyan;
        padding: 0 1;
    }

    #bottom-panel {
        height: auto;
        border: solid yellow;
        min-height: 8;
    }

    #spec-container {
        width: 35%;
        border-right: solid yellow;
    }

    #repl-container {
        width: 65%;
    }

    #spec-content {
        padding: 0 1;
    }

    .spec-label {
        padding: 0 1;
        text-style: bold;
    }

    .component-title {
        padding: 0 1;
        text-style: bold;
        margin-bottom: 1;
    }

    .checklist-item {
        padding: 0 1;
    }

    .tree-item {
        padding: 0 1;
    }

    .card-item {
        padding: 0 1;
    }

    .metric-item {
        padding: 0 1;
        margin-bottom: 1;
    }

    RichLog {
        scrollbar-size: 1 1;
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
        self.iflow = IflowCaller()
        self.memory_system = get_memory_system()
        self.memory = self.memory_system.load_context()
        self.iteration_count = 0
        self.is_running = False
        self.is_paused = False
        self.task = None
        self.start_time = datetime.now()
        self.ai_controller = AIContentController(self)

    def compose(self) -> ComposeResult:
        yield StatusBar(id="status-bar")
        yield Horizontal(
            MonitorPanel(id="monitor-panel"),
            Container(
                LogView(id="log-view"),
                id="log-container"
            ),
            ContentPanel(id="content-panel"),
            id="main-container"
        )
        yield Horizontal(
            SpecQuestionView(id="spec-container"),
            REPLView(on_submit=self._handle_repl_input, id="repl-container"),
            id="bottom-panel"
        )
        yield Footer()

    def on_mount(self) -> None:
        log_view = self.query_one("#log-view", RichLog)
        status_bar = self.query_one("#status-bar", StatusBar)
        content_panel = self.query_one("#content-panel", ContentPanel)
        
        status_bar.start_time = self.start_time
        status_bar.update_display()
        
        self.ai_controller.set_content_panel(content_panel)
        
        log_view.write("[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]")
        log_view.write("[bold cyan]║  🤖 Dev-Bot v2.0 - AI 驱动的自主开发工具                        ║[/bold cyan]")
        log_view.write("[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]")
        log_view.write("")
        log_view.write("[bold green]✓ TUI 模式已启动[/bold green]")
        log_view.write("[yellow]快捷键:[/yellow]")
        log_view.write("  [q] 退出    [Space] 暂停/继续    [c] 清空日志    [h] 帮助")
        log_view.write("")
        log_view.write("[dim]提示: 输入指令开始使用[/dim]")
        log_view.write("")

    async def _handle_repl_input(self, prompt: str) -> None:
        """处理 REPL 输入"""
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(f"[bold cyan]> {prompt}[/bold cyan]")
        
        self.memory_system.add_history_entry("user_input", prompt)
        
        try:
            result = await self.iflow.call(prompt)
            log_view.write(result)
            
            self.memory_system.add_history_entry("ai_output", result[:200])
            
            self.iteration_count += 1
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_iteration(self.iteration_count)
            
            # 尝试解析 AI 返回中的展示命令
            self._parse_ai_display_command(result)
            
        except IflowError as e:
            log_view.write(f"[red]错误: {e}[/red]")
            self.memory_system.add_history_entry("error", str(e))
    
    def _parse_ai_display_command(self, result: str):
        """解析 AI 返回中的展示命令"""
        import json
        import re
        
        # 查找 JSON 格式的展示命令
        pattern = r'\{"action":\s*"[^"]+",\s*"data":\s*\{[^}]*\}\}'
        matches = re.findall(pattern, result)
        
        for match in matches:
            try:
                command = json.loads(match)
                self.ai_controller.handle_ai_command(command)
            except json.JSONDecodeError:
                pass

    def action_toggle_pause(self) -> None:
        """切换暂停状态"""
        self.is_paused = not self.is_paused
        
        status_bar = self.query_one("#status-bar", StatusBar)
        if self.is_paused:
            status_bar.set_status("paused")
            log_view = self.query_one("#log-view", RichLog)
            log_view.write("[yellow]⏸️ 已暂停[/yellow]")
        else:
            status_bar.set_status("running")
            log_view.write("[green]▶️ 继续运行[/green]")

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
        log_view.write("  直接在下方输入框输入指令，按 Enter 发送")
        log_view.write("  示例: '创建任务列表: 编写测试、优化性能'")
        log_view.write("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log_view.write("")

    def on_unmount(self) -> None:
        if self.task:
            self.task.cancel()
        self.iflow.stop()
        
        try:
            self.memory_system.save_context(self.memory)
        except Exception:
            pass


class AIContentController:
    """AI 内容控制器 - 让 AI 可以控制展示方式"""
    
    def __init__(self, app):
        self.app = app
        self.content_panel = None
    
    def set_content_panel(self, panel):
        """设置内容面板"""
        self.content_panel = panel
    
    def handle_ai_command(self, command: dict):
        """处理 AI 指令"""
        if not self.content_panel:
            return
        
        action = command.get("action")
        
        if action == "show_checklist":
            self._show_checklist(command["data"])
        
        elif action == "show_table":
            self._show_table(command["data"])
        
        elif action == "show_tree":
            self._show_tree(command["data"])
        
        elif action == "show_cards":
            self._show_cards(command["data"])
        
        elif action == "show_metrics":
            self._show_metrics(command["data"])
        
        elif action == "clear":
            self.content_panel.clear()
    
    def _show_checklist(self, data: dict):
        """显示检查清单"""
        title = data.get("title", "检查清单")
        items = data.get("items", [])
        self.content_panel.show_checklist(title, items)
    
    def _show_table(self, data: dict):
        """显示表格"""
        title = data.get("title", "表格")
        columns = data.get("columns", [])
        rows = data.get("rows", [])
        self.content_panel.show_table(title, columns, rows)
    
    def _show_tree(self, data: dict):
        """显示树形结构"""
        title = data.get("title", "树形结构")
        items = data.get("items", [])
        self.content_panel.show_tree(title, items)
    
    def _show_cards(self, data: dict):
        """显示卡片"""
        title = data.get("title", "卡片")
        cards = data.get("cards", [])
        self.content_panel.show_cards(title, cards)
    
    def _show_metrics(self, data: dict):
        """显示指标"""
        title = data.get("title", "指标")
        metrics = data.get("metrics", [])
        self.content_panel.show_metrics(title, metrics)


def main():
    """Dev-Bot TUI 主入口"""
    app = DevBotTUI()
    app.run()


if __name__ == "__main__":
    main()


