#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dev-Bot 交互层

统一的多端交互接口：
- TUI（终端用户界面）
- Web（网页端）
- App（移动应用）
"""

import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional
import json


class InteractionMode(Enum):
    """交互模式"""
    TUI = "tui"  # 终端用户界面
    WEB = "web"  # 网页端
    API = "api"  # API 接口
    CLI = "cli"  # 命令行


class InteractionLayer(ABC):
    """交互层抽象基类"""
    
    def __init__(self, mode: InteractionMode):
        self.mode = mode
        self.is_running = False
    
    @abstractmethod
    async def start(self):
        """启动交互层"""
        pass
    
    @abstractmethod
    async def stop(self):
        """停止交互层"""
        pass
    
    @abstractmethod
    async def send_prompt(self, prompt: str, mode: str = "") -> Dict[str, Any]:
        """发送提示词到 iflow"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        pass


class TUILayer(InteractionLayer):
    """TUI 交互层（REPL 模式 + 队列系统 + 输出显示）"""

    def __init__(self):
        super().__init__(InteractionMode.TUI)
        from dev_bot.core import get_core
        from dev_bot.repl_core import REPLCore
        from dev_bot.output_router import get_output_router, OutputSource, LogLevel
        self.core = get_core()
        self.repl = REPLCore()
        self.output_router = get_output_router()
        self._show_queue_status = True
        self._enable_output_display = True  # 改名避免冲突
        self._auto_refresh_interval = 1.0  # 队列状态自动刷新间隔（秒）

        # 订阅输出消息
        self.output_router.subscribe(self._on_output_message)

        # 保存未显示的消息
        self._pending_messages = []

    async def start(self):
        """启动 TUI"""
        self.is_running = True
        print(f"[TUI] 启动 REPL 模式终端用户界面...")

        # 启动 REPL 核心
        await self.repl.start()

        # REPL 主循环
        while self.is_running:
            try:
                # 显示队列状态
                if self._show_queue_status:
                    await self._display_queue_status()

                # 显示提示符
                cmd = input("dev-bot> ").strip()

                if not cmd:
                    continue

                # 解析命令
                if cmd in ["exit", "quit", "q"]:
                    break

                if cmd in ["help", "h", "?"]:
                    self._show_help()
                    continue

                if cmd == "status" or cmd == "s":
                    await self._display_detailed_status()
                    continue

                if cmd == "clear" or cmd == "c":
                    cleared = await self.repl.clear_completed()
                    print(f"[TUI] 清理完成: {cleared}")
                    continue

                if cmd == "queue" or cmd == "q":
                    await self._display_queue_status()
                    continue

                if cmd.startswith("input "):
                    # 提供输入
                    parts = cmd.split(" ", 2)
                    if len(parts) >= 2:
                        input_id = parts[1]
                        value = parts[2] if len(parts) > 2 else input(f"输入值> ")
                        success = await self.repl.provide_input(input_id, value)
                        if success:
                            print(f"[TUI] 输入已提供: {input_id}")
                        else:
                            print(f"[TUI] 输入失败: {input_id} 不存在")
                    continue

                # 输出显示命令
                if cmd == "output" or cmd == "o":
                    await self._show_output()
                    continue

                if cmd.startswith("output "):
                    parts = cmd.split(" ", 2)
                    if len(parts) >= 2:
                        if parts[1] == "clear":
                            await self._clear_output()
                        else:
                            await self._show_output(
                                source=parts[1] if len(parts) > 1 else None,
                                count=20
                            )
                    continue

                # 对话命令
                if cmd.startswith("dialogue ") or cmd.startswith("dlg "):
                    # 对话相关命令
                    dlg_cmd = cmd.replace("dialogue ", "").replace("dlg ", "")
                    
                    if dlg_cmd.startswith("create ") or dlg_cmd.startswith("new "):
                        # 创建对话：dlg create <task_id> [participants]
                        parts = dlg_cmd.replace("create ", "").replace("new ", "").split()
                        if len(parts) >= 1:
                            task_id = parts[0]
                            participants = parts[1:] if len(parts) > 1 else None
                            
                            # 使用对话整合器创建对话
                            from dev_bot.dialogue_integrator import DialogueIntegrator
                            integrator = DialogueIntegrator()
                            dialogue_id = await integrator.create_dialogue_from_queue(task_id, participants)
                            
                            if dialogue_id:
                                print(f"[TUI] 对话已创建: {dialogue_id}")
                            else:
                                print(f"[TUI] 对话创建失败: 任务 {task_id} 不存在")
                        else:
                            print("[TUI] 用法: dialogue create <task_id> [participants]")
                        continue
                    
                    if dlg_cmd.startswith("send ") or dlg_cmd.startswith("say "):
                        # 发送消息：dlg send <dialogue_id> <message>
                        parts = dlg_cmd.replace("send ", "").replace("say ", "").split(" ", 1)
                        if len(parts) == 2:
                            dialogue_id = parts[0]
                            message = parts[1]
                            
                            # 使用对话整合器添加用户消息
                            from dev_bot.dialogue_integrator import DialogueIntegrator
                            integrator = DialogueIntegrator()
                            success = await integrator.add_user_message(message, dialogue_id)
                            
                            if success:
                                print(f"[TUI] 消息已发送到对话 {dialogue_id}")
                            else:
                                print(f"[TUI] 消息发送失败: 对话 {dialogue_id} 不存在")
                        else:
                            print("[TUI] 用法: dialogue send <dialogue_id> <message>")
                        continue
                    
                    if dlg_cmd.startswith("info ") or dlg_cmd.startswith("show "):
                        # 显示对话信息：dlg info <dialogue_id>
                        parts = dlg_cmd.replace("info ", "").replace("show ", "").split()
                        if len(parts) >= 1:
                            dialogue_id = parts[0]
                            await self._display_dialogue_info(dialogue_id)
                        else:
                            print("[TUI] 用法: dialogue info <dialogue_id>")
                        continue
                    
                    if dlg_cmd == "list" or dlg_cmd == "ls":
                        # 列出所有对话
                        await self._display_dialogue_list()
                        continue
                    
                    if dlg_cmd.startswith("run ") or dlg_cmd.startswith("start "):
                        # 运行对话：dlg run <dialogue_id>
                        parts = dlg_cmd.replace("run ", "").replace("start ", "").split()
                        if len(parts) >= 1:
                            dialogue_id = parts[0]
                            await self._run_dialogue(dialogue_id)
                        else:
                            print("[TUI] 用法: dialogue run <dialogue_id>")
                        continue
                    
                    # 显示对话帮助
                    print("[TUI] 对话命令:")
                    print("  dialogue create <task_id> [participants] - 从任务创建对话")
                    print("  dialogue send <dialogue_id> <message> - 发送消息到对话")
                    print("  dialogue info <dialogue_id> - 显示对话信息")
                    print("  dialogue list - 列出所有对话")
                    print("  dialogue run <dialogue_id> - 运行对话")
                    continue

                # 提交问题
                mode = ""
                prompt = cmd

                if cmd.startswith("--plan "):
                    mode = "--plan"
                    prompt = cmd[7:]
                elif cmd.startswith("-y "):
                    mode = "-y"
                    prompt = cmd[3:]
                elif cmd.startswith("--thinking "):
                    mode = "--thinking"
                    prompt = cmd[12:]

                # 提交到问题队列
                question_id = await self.repl.submit_question(prompt, mode)
                print(f"[TUI] 问题已提交: {question_id}")

            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n[TUI] 中断")
                break

        # 停止 REPL
        await self.repl.stop()

    async def stop(self):
        """停止 TUI"""
        self.is_running = False
        await self.repl.stop()
        print(f"[TUI] 停止 REPL 模式终端用户界面")

    async def send_prompt(self, prompt: str, mode: str = "") -> Dict[str, Any]:
        """发送提示词"""
        if mode == "plan":
            return await self.core.plan(prompt)
        elif mode == "execute":
            return await self.core.execute(prompt)
        elif mode == "think":
            return await self.core.think(prompt)
        else:
            return await self.core.call_iflow(prompt)

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "mode": self.mode.value,
            "is_running": self.is_running,
            "core_status": self.core.get_status(),
            "repl_running": self.repl._running if self.repl else False
        }

    async def _display_queue_status(self):
        """显示队列状态"""
        status = await self.repl.get_queue_status()

        q_status = status["question_queue"]
        i_status = status["input_queue"]

        print(f"\n[队列状态]")
        print(f"  问题队列: {q_status['pending']} 待处理 | {q_status['processing']} 处理中 | {q_status['completed']} 已完成 | {q_status['failed']} 失败")
        print(f"  输入队列: {i_status['pending']} 待输入 | {i_status['provided']} 已提供 | {i_status['consumed']} 已消费")

        # 显示待处理的问题
        if q_status["pending"] > 0:
            print(f"\n[待处理问题]")
            for q in q_status["questions"][-5:]:  # 显示最近 5 个
                if q["status"] == "pending":
                    prompt_preview = q["prompt"][:50] + "..." if len(q["prompt"]) > 50 else q["prompt"]
                    print(f"  [{q['id']}] {prompt_preview}")

        # 显示待处理的输入
        if i_status["pending"] > 0:
            print(f"\n[待输入]")
            for i in i_status["inputs"][-5:]:  # 显示最近 5 个
                if i["status"] == "pending":
                    print(f"  [{i['id']}] {i['prompt']}")
                    print(f"    命令: input {i['id']} <值>")

        print()  # 空行

    async def _display_detailed_status(self):
        """显示详细状态"""
        status = await self.repl.get_queue_status()

        print(f"\n[详细状态]")
        print(f"  核心状态: {self.core.get_status()}")
        print(f"  REPL 运行中: {self.repl._running}")

        # 问题队列详情
        q_status = status["question_queue"]
        print(f"\n[问题队列详情]")
        print(f"  总计: {q_status['total']}")
        print(f"  待处理: {q_status['pending']}")
        print(f"  处理中: {q_status['processing']}")
        print(f"  已完成: {q_status['completed']}")
        print(f"  失败: {q_status['failed']}")

        if q_status["questions"]:
            print(f"\n[问题列表]")
            for q in q_status["questions"][-10:]:  # 显示最近 10 个
                status_symbol = {
                    "pending": "⏳",
                    "processing": "🔄",
                    "completed": "✅",
                    "failed": "❌"
                }.get(q["status"], "?")
                prompt_preview = q["prompt"][:60] + "..." if len(q["prompt"]) > 60 else q["prompt"]
                print(f"  {status_symbol} [{q['id']}] {prompt_preview}")

        # 输入队列详情
        i_status = status["input_queue"]
        print(f"\n[输入队列详情]")
        print(f"  总计: {i_status['total']}")
        print(f"  待输入: {i_status['pending']}")
        print(f"  已提供: {i_status['provided']}")
        print(f"  已消费: {i_status['consumed']}")

        if i_status["inputs"]:
            print(f"\n[输入列表]")
            for i in i_status["inputs"][-10:]:  # 显示最近 10 个
                status_symbol = {
                    "pending": "⏳",
                    "provided": "✅",
                    "consumed": "✅"
                }.get(i["status"], "?")
                print(f"  {status_symbol} [{i['id']}] {i['prompt']}")

        print()

    def _show_help(self):
        """显示帮助"""
        print("""
Dev-Bot REPL 模式帮助：
  提交问题：
    <prompt>              - 普通模式提交
    --plan <prompt>       - 规划模式（只分析不执行）
    -y <prompt>           - 执行模式（直接执行）
    --thinking <prompt>   - 思考模式（更全面）

  对话系统：
    dialogue create <task_id> [participants] - 从任务创建对话
    dialogue send <dialogue_id> <message>    - 发送消息到对话
    dialogue info <dialogue_id>              - 显示对话信息
    dialogue list / ls                       - 列出所有对话
    dialogue run <dialogue_id>               - 运行对话

  队列管理：
    status / s            - 查看详细状态
    queue / q             - 查看队列状态
    clear / c             - 清理已完成任务
    input <id> <value>    - 提供输入

  输出显示：
    output / o            - 查看最新输出
    output guardian       - 查看 AI 守护输出
    output ai_loop        - 查看 AI 循环输出
    output error          - 查看错误输出
    output clear          - 清空输出历史

  其他：
    help / h / ?          - 显示帮助
    exit / quit / q       - 退出 REPL
        """)

    def _on_output_message(self, message):
        """处理输出消息"""
        if not self._enable_output_display:
            self._pending_messages.append(message)
            return

        self._display_output_message(message)

    def _display_output_message(self, message):
        """显示输出消息"""
        from dev_bot.output_router import OutputSource, LogLevel

        # 源标识
        source_symbol = {
            OutputSource.GUARDIAN: "🛡️",
            OutputSource.AI_LOOP: "🔄",
            OutputSource.SYSTEM: "⚙️"
        }.get(message.source, "?")

        # 级别标识
        level_symbol = {
            LogLevel.DEBUG: "🔍",
            LogLevel.INFO: "ℹ️",
            LogLevel.WARNING: "⚠️",
            LogLevel.ERROR: "❌",
            LogLevel.SUCCESS: "✅"
        }.get(message.level, "?")

        # 颜色代码
        color_code = {
            LogLevel.ERROR: "\033[31m",  # 红色
            LogLevel.WARNING: "\033[33m",  # 黄色
            LogLevel.SUCCESS: "\033[32m",  # 绿色
            LogLevel.INFO: "\033[36m",  # 青色
            LogLevel.DEBUG: "\033[90m"  # 灰色
        }.get(message.level, "\033[0m")

        reset_code = "\033[0m"

        # 显示消息
        print(f"{color_code}{source_symbol} {level_symbol} [{message.source.value.upper()}] {message.message}{reset_code}")

    async def _show_output(self, source=None, level=None, count=20):
        """显示输出

        Args:
            source: 输出源过滤
            level: 日志级别过滤
            count: 显示数量
        """
        from dev_bot.output_router import OutputSource, LogLevel

        # 解析参数
        if source:
            if source == "guardian":
                source_filter = OutputSource.GUARDIAN
            elif source == "ai_loop":
                source_filter = OutputSource.AI_LOOP
            elif source == "system":
                source_filter = OutputSource.SYSTEM
            else:
                source_filter = None
        else:
            source_filter = None

        if level:
            if level == "error":
                level_filter = LogLevel.ERROR
            elif level == "warning":
                level_filter = LogLevel.WARNING
            elif level == "success":
                level_filter = LogLevel.SUCCESS
            elif level == "info":
                level_filter = LogLevel.INFO
            elif level == "debug":
                level_filter = LogLevel.DEBUG
            else:
                level_filter = None
        else:
            level_filter = None

        # 获取消息
        messages = await self.output_router.get_messages(
            source=source_filter,
            level=level_filter,
            limit=count
        )

        # 显示
        print(f"\n[输出显示] 共 {len(messages)} 条消息\n")

        for msg in messages:
            self._display_output_message(msg)

        print()

    async def _clear_output(self):
        """清空输出历史"""
        await self.output_router.clear()
        print("[TUI] 输出历史已清空")

    async def _display_dialogue_list(self):
        """显示所有对话列表"""
        from dev_bot.dialogue_integrator import DialogueIntegrator

        integrator = DialogueIntegrator()
        dialogues = await integrator.list_dialogues()

        if not dialogues:
            print("[TUI] 没有活跃的对话")
            return

        print(f"\n[对话列表] 共 {len(dialogues)} 个对话\n")

        for idx, dialogue in enumerate(dialogues, 1):
            print(f"{idx}. ID: {dialogue.id}")
            print(f"   主题: {dialogue.topic}")
            print(f"   状态: {dialogue.status}")
            print(f"   参与者: {', '.join([p.name for p in dialogue.participants.values()])}")
            print(f"   消息数: {len(dialogue.messages)}")
            print(f"   创建时间: {dialogue.created_at}")
            print()

    async def _display_dialogue_info(self, dialogue_id: str):
        """显示对话详情"""
        from dev_bot.dialogue_integrator import DialogueIntegrator

        integrator = DialogueIntegrator()
        dialogue = await integrator.get_dialogue(dialogue_id)

        if not dialogue:
            print(f"[TUI] 对话 {dialogue_id} 不存在")
            return

        print(f"\n[对话详情]\n")
        print(f"ID: {dialogue.id}")
        print(f"主题: {dialogue.topic}")
        print(f"状态: {dialogue.status}")
        print(f"创建时间: {dialogue.created_at}")
        print(f"最后更新: {dialogue.updated_at}")

        print(f"\n参与者:")
        for role_id, participant in dialogue.participants.items():
            print(f"  - {participant.name} (ID: {role_id})")

        print(f"\n消息 ({len(dialogue.messages)} 条):")
        for msg in dialogue.messages:
            speaker = dialogue.participants.get(msg.speaker, msg.speaker)
            print(f"  [{speaker}]: {msg.content[:100]}{'...' if len(msg.content) > 100 else ''}")

        print()

    async def _run_dialogue(self, dialogue_id: str):
        """运行对话"""
        from dev_bot.dialogue_integrator import DialogueIntegrator

        print(f"\n[TUI] 启动对话 {dialogue_id}...")

        integrator = DialogueIntegrator()
        success = await integrator.run_dialogue(dialogue_id)

        if success:
            print(f"[TUI] 对话 {dialogue_id} 完成")
            # 显示对话结果
            await self._display_dialogue_info(dialogue_id)
        else:
            print(f"[TUI] 对话 {dialogue_id} 运行失败")

    def _toggle_output_display(self):
        """切换输出显示"""
        self._enable_output_display = not self._enable_output_display

        if self._enable_output_display:
            print(f"[TUI] 输出显示已启用（{len(self._pending_messages)} 条待显示消息）")
            # 显示待显示的消息
            for msg in self._pending_messages:
                self._display_output_message(msg)
            self._pending_messages.clear()
        else:
            print("[TUI] 输出显示已禁用")


class WebLayer(InteractionLayer):
    """Web 交互层（极简 HTTP 服务）"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        super().__init__(InteractionMode.WEB)
        self.host = host
        self.port = port
        from dev_bot.core import get_core
        self.core = get_core()
        self.server = None
    
    async def start(self):
        """启动 Web 服务"""
        self.is_running = True
        print(f"[Web] 启动网页服务（{self.host}:{self.port}）...")
        
        # 极简 HTTP 服务器
        import socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        server.setblocking(False)
        
        self.server = server
        
        # 接受连接循环
        loop = asyncio.get_event_loop()
        
        try:
            while self.is_running:
                try:
                    client, addr = await loop.sock_accept(server)
                    asyncio.create_task(self._handle_client(client, addr))
                except BlockingIOError:
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[Web] 服务错误: {e}")
        finally:
            server.close()
    
    async def _handle_client(self, client, addr):
        """处理客户端请求"""
        try:
            data = await asyncio.get_event_loop().sock_recv(client, 4096)
            request = data.decode('utf-8', errors='ignore')
            
            # 极简的 HTTP 解析
            if "GET " in request:
                response = self._get_index_page()
                client.sendall(response.encode())
            elif "POST " in request:
                # 解析 POST body
                body_start = request.find("\r\n\r\n")
                if body_start > 0:
                    body = request[body_start + 4:]
                    try:
                        data = json.loads(body)
                        prompt = data.get("prompt", "")
                        mode = data.get("mode", "")
                        
                        # 调用 iflow
                        result = await self.send_prompt(prompt, mode)
                        
                        # 返回 JSON 响应
                        response_body = json.dumps(result, ensure_ascii=False)
                        response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(response_body)}\r\n\r\n{response_body}"
                        client.sendall(response.encode())
                    except:
                        pass
        except:
            pass
        finally:
            client.close()
    
    def _get_index_page(self) -> str:
        """获取首页"""
        return f"""HTTP/1.1 200 OK\r
Content-Type: text/html; charset=utf-8\r
\r
<!DOCTYPE html>
<html>
<head>
    <title>Dev-Bot Web</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
        .container {{ display: flex; flex-direction: column; gap: 20px; }}
        textarea {{ width: 100%; height: 150px; padding: 10px; }}
        select {{ padding: 10px; }}
        button {{ padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }}
        button:hover {{ background: #0056b3; }}
        #result {{ padding: 15px; background: #f5f5f5; border-radius: 5px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>Dev-Bot Web 界面</h1>
    <div class="container">
        <div>
            <label>模式：</label>
            <select id="mode">
                <option value="">普通模式</option>
                <option value="--plan">规划模式</option>
                <option value="-y">执行模式</option>
                <option value="--thinking">思考模式</option>
            </select>
        </div>
        <div>
            <label>提示词：</label>
            <textarea id="prompt" placeholder="输入提示词..."></textarea>
        </div>
        <button onclick="send()">发送</button>
        <div id="result">等待结果...</div>
    </div>
    <script>
        async function send() {{
            const prompt = document.getElementById('prompt').value;
            const mode = document.getElementById('mode').value;
            const result = document.getElementById('result');
            
            result.textContent = '处理中...';
            
            const response = await fetch('/', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ prompt, mode }})
            }});
            
            const data = await response.json();
            
            if (data.success) {{
                result.textContent = `成功（${{data.duration}}秒）\n\n${{data.output}}`;
            }} else {{
                result.textContent = `失败：${{data.error}}`;
            }}
        }}
    </script>
</body>
</html>
"""
    
    async def stop(self):
        """停止 Web 服务"""
        self.is_running = False
        if self.server:
            self.server.close()
        print(f"[Web] 停止网页服务")
    
    async def send_prompt(self, prompt: str, mode: str = "") -> Dict[str, Any]:
        """发送提示词"""
        if mode == "--plan":
            return await self.core.plan(prompt)
        elif mode == "-y":
            return await self.core.execute(prompt)
        elif mode == "--thinking":
            return await self.core.think(prompt)
        else:
            return await self.core.call_iflow(prompt)
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "mode": self.mode.value,
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "core_status": self.core.get_status()
        }


class APILayer(InteractionLayer):
    """API 交互层（极简 REST API）"""
    
    def __init__(self):
        super().__init__(InteractionMode.API)
        from dev_bot.core import get_core
        self.core = get_core()
        self.web_layer = WebLayer()
    
    async def start(self):
        """启动 API 服务"""
        await self.web_layer.start()
    
    async def stop(self):
        """停止 API 服务"""
        await self.web_layer.stop()
    
    async def send_prompt(self, prompt: str, mode: str = "") -> Dict[str, Any]:
        """发送提示词"""
        return await self.web_layer.send_prompt(prompt, mode)
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "mode": self.mode.value,
            "is_running": self.is_running,
            "web_status": self.web_layer.get_status()
        }


class InteractionManager:
    """交互管理器
    
    统一管理所有交互层
    """
    
    def __init__(self):
        self.layers: Dict[InteractionMode, InteractionLayer] = {}
        self.active_layer: Optional[InteractionLayer] = None
        
        print(f"[交互管理器] 初始化完成")
    
    async def start_tui(self):
        """启动 TUI"""
        layer = TUILayer()
        self.layers[InteractionMode.TUI] = layer
        self.active_layer = layer
        await layer.start()
    
    async def start_web(self, host: str = "127.0.0.1", port: int = 8080):
        """启动 Web"""
        layer = WebLayer(host, port)
        self.layers[InteractionMode.WEB] = layer
        self.active_layer = layer
        await layer.start()
    
    async def start_api(self, host: str = "127.0.0.1", port: int = 8080):
        """启动 API"""
        layer = APILayer()
        self.layers[InteractionMode.API] = layer
        self.active_layer = layer
        await layer.start()
    
    async def stop(self):
        """停止当前交互层"""
        if self.active_layer:
            await self.active_layer.stop()
            self.active_layer = None
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "active_mode": self.active_layer.mode.value if self.active_layer else None,
            "is_running": self.active_layer.is_running if self.active_layer else False,
            "layers": {mode.value: layer.get_status() for mode, layer in self.layers.items()}
        }


# 全局交互管理器实例
_global_interaction_manager = None


def get_interaction_manager() -> InteractionManager:
    """获取全局交互管理器实例"""
    global _global_interaction_manager
    
    if _global_interaction_manager is None:
        _global_interaction_manager = InteractionManager()
    
    return _global_interaction_manager


def reset_interaction_manager():
    """重置全局交互管理器"""
    global _global_interaction_manager
    _global_interaction_manager = None
