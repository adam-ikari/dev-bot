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

from dev_bot import IflowCaller, get_memory_system
from dev_bot.iflow import IflowError, IflowTokenExpiredError, IflowMemoryError


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
        
        content = f"""CPU: {cpu_percent}%
{"█" * int(cpu_percent // 5)}{" " * (15 - int(cpu_percent // 5))}

MEM: {memory_mb:.0f} MB
{"█" * int((memory_mb / 2048) * 15)}

⏱ {elapsed_str}"""
        
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
        height: 1;
    }

    #main-container {
        height: 1fr;
        min-height: 10;
    }

    #log-container {
        height: 1fr;
        border: solid green;
    }

    #monitor-panel {
        width: 15;
        border: solid blue;
        padding: 0 0;
    }

    #content-panel {
        width: 20;
        border: solid cyan;
        padding: 0 0;
    }

    #bottom-panel {
        height: 3;
        border: solid yellow;
    }

    #spec-container {
        width: 35%;
    }

    #repl-container {
        width: 65%;
    }

    #spec-content {
        padding: 0 0;
    }

    .spec-label {
        padding: 0 0;
        text-style: bold;
    }

    .component-title {
        padding: 0 0;
        text-style: bold;
        margin-bottom: 0;
    }

    .checklist-item {
        padding: 0 0;
    }

    .tree-item {
        padding: 0 0;
    }

    .card-item {
        padding: 0 0;
    }

    .metric-item {
        padding: 0 0;
        margin-bottom: 0;
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
        self.ai_iteration_count = 0
        self.is_paused = False
        self.ai_loop_stopped = False
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

    def on_mount(self) -> None:
        log_view = self.query_one("#log-view", RichLog)
        status_bar = self.query_one("#status-bar", StatusBar)
        content_panel = self.query_one("#content-panel", ContentPanel)

        status_bar.start_time = self.start_time
        status_bar.set_status("running")
        status_bar.set_message("AI 正在自主工作")

        self.ai_controller.set_content_panel(content_panel)

        log_view.write("[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]")
        log_view.write("[bold cyan]║  🤖 Dev-Bot v2.0 - AI 驱动的自主开发工具                        ║[/bold cyan]")
        log_view.write("[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]")
        log_view.write("")

        # 启动 AI 自动分析任务
        self.set_interval(1, self._auto_ai_loop)

    async def _handle_repl_input(self, prompt: str) -> None:
        """处理 REPL 输入 - 用户指令，不影响 AI 自主工作"""
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(f"[bold cyan]> 用户指令: {prompt}[/bold cyan]")

        self.memory_system.add_history_entry("user_input", prompt)

        # 检查是否是 restart 命令
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

        try:
            result = await self.iflow.call(prompt)
            log_view.write(result)

            self.memory_system.add_history_entry("ai_output", result[:200])

            # 用户输入不影响 AI 迭代计数
            # AI 继续自主工作

            # 尝试解析 AI 返回中的展示命令
            self._parse_ai_display_command(result)

        except IflowTokenExpiredError as e:
            log_view.write(f"[red]❌ iflow 令牌过期[/red]")
            log_view.write("[yellow]请执行以下命令重新授权:[/yellow]")
            log_view.write("[bold cyan]  iflow auth[/bold cyan]")
            log_view.write("")
            log_view.write("[dim]授权后按 [Space] 继续 AI 工作[/dim]")
            
            self.is_paused = True
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_status("paused")
            status_bar.set_message("令牌过期，需要重新授权")
            
            self.memory_system.add_history_entry("error", f"令牌过期: {e}")
        except IflowMemoryError as e:
            log_view.write("[red]内存不足: iflow 进程内存不足[/red] [dim]修复后输入: restart[/dim]")
            
            self.ai_loop_stopped = True
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_status("stopped")
            status_bar.set_message("内存不足")
            
            self.memory_system.add_history_entry("error", f"内存错误: {e}")
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

    async def _auto_ai_loop(self) -> None:
        """自动 AI 循环 - 独立运行，不依赖用户输入"""
        if self.is_paused:
            return
        
        # 如果 AI 循环因错误停止，不再继续
        if self.ai_loop_stopped:
            return

        self.ai_iteration_count += 1
        log_view = self.query_one("#log-view", RichLog)
        log_view.write(f"[yellow]🔄 AI 分析 #{self.ai_iteration_count}[/yellow]")

        # 构建 AI 提示
        project_path = Path.cwd()
        memory_summary = self.memory_system.get_context_summary()

        prompt = f"""你是 Dev-Bot，一个 AI 驱动的自主开发代理。

## 项目信息
- 项目路径: {project_path}
- 技术栈: Python 3.9+, asyncio
- 代码风格: PEP 8, 4空格缩进
- 当前迭代: #{self.ai_iteration_count}

## 你的使命
分析当前项目 → 做出决策 → 执行开发 → 验证结果 → 继续改进

## 当前状态
{memory_summary}

## 工作原则
1. 先分析，后行动 - 每次修改前先阅读相关代码
2. 小步快跑，频繁验证 - 每次只修改一个功能点
3. 遇到错误立即停止 - 分析错误原因，不要盲目重试
4. 修改代码后必须测试 - 使用 pytest 运行相关测试
5. 代码审查 - 修改后检查是否引入新问题
6. 完全自主工作 - 不需要用户干预，自己决策、自己执行

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

        try:
            result = await self.iflow.call(prompt)
            log_view.write(result)

            # 记录到历史
            self.memory_system.add_history_entry("ai_analysis", result[:200])

            # 解析展示命令
            self._parse_ai_display_command(result)

            # 更新迭代计数显示
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_iteration(self.ai_iteration_count)

        except IflowTokenExpiredError as e:
            log_view.write(f"[red]❌ iflow 令牌过期[/red]")
            log_view.write("[yellow]请执行以下命令重新授权:[/yellow]")
            log_view.write("[bold cyan]  iflow auth[/bold cyan]")
            log_view.write("")
            log_view.write("[dim]授权后按 [Space] 继续 AI 工作[/dim]")
            
            self.is_paused = True
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_status("paused")
            status_bar.set_message("令牌过期，需要重新授权")
            
            self.memory_system.add_history_entry("error", f"令牌过期: {e}")
        except IflowMemoryError as e:
            log_view.write("[red]内存不足: iflow 进程内存不足[/red] [dim]修复后输入: restart[/dim]")
            
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
        log_view.write("  直接在下方输入框输入指令，按 Enter 发送")
        log_view.write("  示例: '创建任务列表: 编写测试、优化性能'")
        log_view.write("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log_view.write("")

    def on_unmount(self) -> None:
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


