#!/usr/bin/env python3

"""
Dev-Bot 核心 - AI 驱动的 Spec 开发系统

专注于核心功能：
1. Spec 驱动开发
2. AI 循环
3. REPL 模式
4. 自动修复
5. 自动重启

"""

import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dev_bot.ai_prompts import (
    get_decision_prompt,
    get_restart_strategy_prompt,
    get_spec_code_consistency_prompt,
)


class AIOrchestrator:
    """AI 协调器 - 管理所有 AI 交互"""

    def __init__(self, ai_command: str = "iflow", ai_args: List[str] = None, log_dir: Optional[Path] = None):
        self.ai_command = ai_command
        self.ai_args = ai_args or []
        self.session_counter = 0
        self.log_dir = log_dir or Path(".ai-logs")
        # 确保日志目录及其父目录都存在
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def call_ai(self, prompt: str, timeout: int = 120) -> Optional[str]:
        """调用 AI 工具"""
        try:
            result = subprocess.run(
                [self.ai_command] + self.ai_args,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"[!] AI 调用失败: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print("[!] AI 调用超时")
            return None
        except Exception as e:
            print(f"[!] AI 调用异常: {e}")
            return None

    def call_and_log(self, prompt: str, session_num: int) -> Optional[str]:
        """调用 AI 并记录日志"""
        self.session_counter += 1

        # 创建日志文件
        log_file = self.log_dir / f"session_{session_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"{'='*60}\n")
            f.write(f"Session #{session_num}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"Prompt:\n{prompt}\n\n")
            f.write(f"{'='*60}\n\n")

        # 调用 AI
        output = self.call_ai(prompt)

        if output:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"AI Output:\n{output}\n\n")

        return output


class REPLManager:
    """REPL 管理器 - 非阻塞用户输入"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.input_file = self.project_root / ".dev-bot-cache" / "user_inputs.txt"
        self.input_file.parent.mkdir(parents=True, exist_ok=True)
        self.inputs: List[str] = []
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        """启动输入监控"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_inputs, daemon=True)
        self.thread.start()

    def stop(self):
        """停止输入监控"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def _monitor_inputs(self):
        """监控输入文件"""
        last_size = 0

        while self.running:
            try:
                if self.input_file.exists():
                    current_size = self.input_file.stat().st_size

                    if current_size > last_size:
                        # 读取新内容
                        with open(self.input_file, encoding='utf-8') as f:
                            f.seek(last_size)
                            new_content = f.read().strip()

                            if new_content:
                                self.inputs.append(new_content)
                                # 保留最近 50 条
                                if len(self.inputs) > 50:
                                    self.inputs = self.inputs[-50:]

                        last_size = current_size
            except Exception:
                pass

            time.sleep(0.5)

    def get_recent_inputs(self, count: int = 5) -> List[str]:
        """获取最近的输入"""
        return self.inputs[-count:] if self.inputs else []

    def get_inputs(self) -> List[str]:
        """获取所有输入"""
        return self.inputs.copy()

    def has_inputs(self) -> bool:
        """检查是否有输入"""
        return len(self.inputs) > 0

    def clear_inputs(self):
        """清空输入列表"""
        self.inputs = []

    def add_input(self, text: str):
        """添加输入（用于测试）"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.input_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {text}\n")
        self.inputs.append(text)


class SpecManager:
    """Spec 管理器 - 处理 Spec 相关操作"""

    def __init__(self, project_root: Path):
        self.specs_dir = project_root / "specs"
        self.specs_dir.mkdir(exist_ok=True)

    def load_specs(self) -> List[Dict[str, Any]]:
        """加载所有 Spec"""
        specs = []
        for spec_file in self.specs_dir.glob("*.json"):
            try:
                with open(spec_file, encoding='utf-8') as f:
                    spec = json.load(f)
                    spec['_file'] = str(spec_file)
                    specs.append(spec)
            except Exception as e:
                print(f"[!] 加载 Spec 失败 {spec_file}: {e}")
        return specs

    def validate_specs(self) -> Dict[str, Any]:
        """验证 Spec"""
        specs = self.load_specs()
        issues = []

        for spec in specs:
            # 检查必需字段
            required_fields = ['spec_version', 'metadata']
            for field in required_fields:
                if field not in spec:
                    issues.append(f"{spec.get('_file', 'unknown')}: 缺少字段 {field}")

            # 检查 metadata
            metadata = spec.get('metadata', {})
            if not metadata.get('name'):
                issues.append(f"{spec.get('_file', 'unknown')}: metadata 缺少 name")

            if not metadata.get('type'):
                issues.append(f"{spec.get('_file', 'unknown')}: metadata 缺少 type")

        return {
            'total': len(specs),
            'valid': len(specs) - len(issues),
            'issues': issues
        }

    def get_spec_content_summary(self) -> str:
        """获取 Spec 内容摘要"""
        specs = self.load_specs()
        summary = []

        for spec in specs:
            metadata = spec.get('metadata', {})
            name = metadata.get('name', 'Unknown')
            spec_type = metadata.get('type', 'Unknown')
            description = metadata.get('description', 'No description')

            summary.append(f"## {name} ({spec_type})")
            summary.append(f"描述: {description}")

            # 添加关键信息
            if 'requirements' in spec:
                summary.append(f"需求: {', '.join(spec['requirements'][:3])}")
            if 'features' in spec:
                summary.append(f"功能: {', '.join(spec['features'][:3])}")

            summary.append("")

        return "\n".join(summary)

    def analyze_spec_code_consistency(self, code_summary: str, ai_orchestrator: 'AIOrchestrator', tech_stack: str) -> Dict[str, Any]:
        """分析 Spec 和代码的一致性"""

        spec_content = self.get_spec_content_summary()

        if not spec_content:
            return {
                'is_consistent': True,
                'consistency_score': 1.0,
                'issues': [],
                'summary': '没有 Spec 文件',
                'recommendation': '建议创建 Spec 文件'
            }

        prompt = get_spec_code_consistency_prompt(
            spec_content=spec_content,
            code_summary=code_summary,
            tech_stack=tech_stack
        )

        output = ai_orchestrator.call_ai(prompt)

        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                print("[!] Spec 和代码一致性分析结果解析失败")
                return {
                    'is_consistent': True,
                    'consistency_score': 1.0,
                    'issues': [],
                    'summary': '无法解析分析结果',
                    'recommendation': '手动检查'
                }
        else:
            return {
                'is_consistent': True,
                'consistency_score': 1.0,
                'issues': [],
                'summary': 'AI 调用失败',
                'recommendation': '手动检查'
            }


class AutoFixer:
    """自动修复器 - 自动修复代码问题"""

    def __init__(self, ai_orchestrator: AIOrchestrator):
        self.ai = ai_orchestrator

    def fix_errors(self, errors: List[str]) -> bool:
        """自动修复错误"""
        if not errors:
            return True

        print(f"[ℹ️] 尝试自动修复 {len(errors)} 个错误...")

        # 使用 AI 生成修复方案
        prompt = f"""你是 Dev-Bot 的自动修复助手。以下是需要修复的错误：

{chr(10).join(f'- {error}' for error in errors)}

请分析这些错误并提供修复方案。以 JSON 格式返回：

{{
  "can_fix": true/false,
  "fix_commands": ["命令1", "命令2"],
  "manual_steps": ["步骤1", "步骤2"],
  "reason": "修复原因"
}}

只返回 JSON，不要有任何其他文字。
"""

        output = self.ai.call_ai(prompt)

        if output:
            try:
                # 解析 JSON
                if output.startswith('```'):
                    lines = output.split('\n')
                    if lines[0].startswith('```'):
                        output = '\n'.join(lines[1:])
                    if output.endswith('```'):
                        output = output[:-3]
                    output = output.strip()

                fix_plan = json.loads(output)

                if fix_plan.get('can_fix'):
                    # 执行修复命令
                    for cmd in fix_plan.get('fix_commands', []):
                        print(f"[ℹ️] 执行修复命令: {cmd}")
                        try:
                            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                            if result.returncode != 0:
                                print(f"[!] 修复失败: {result.stderr}")
                                return False
                        except Exception as e:
                            print(f"[!] 修复异常: {e}")
                            return False

                    print("[✅] 自动修复完成")
                    return True
                else:
                    print(f"[!] 无法自动修复: {fix_plan.get('reason', 'unknown')}")
                    return False

            except json.JSONDecodeError as e:
                print(f"[!] 解析修复方案失败: {e}")
                return False

        return False


class AutoRestarter:
    """自动重启器 - 智能重启管理"""

    def __init__(self, ai_orchestrator: AIOrchestrator, project_root: Path):
        self.ai = ai_orchestrator
        self.project_root = project_root
        self.restart_info_file = project_root / ".dev-bot-cache/restart_info.json"
        self.restart_history_file = project_root / ".dev-bot-cache/restart_history.json"
        self.crash_log_dir = project_root / ".crash-logs"
        self.crash_log_dir.mkdir(exist_ok=True)
        (project_root / ".dev-bot-cache").mkdir(exist_ok=True)

    def record_startup(self, command: str, args: List[str]):
        """记录启动信息"""
        restart_info = {
            "command": command,
            "args": args,
            "working_directory": str(self.project_root),
            "startup_time": datetime.now().isoformat(),
            "pid": os.getpid(),
            "restart_count": self._get_restart_count() + 1
        }

        with open(self.restart_info_file, 'w', encoding='utf-8') as f:
            json.dump(restart_info, f, indent=2, ensure_ascii=False)

    def analyze_and_restart(self, error_type: str, error_message: str, traceback: str) -> bool:
        """分析错误并决定是否重启"""
        print("[ℹ️] 使用 AI 分析重启策略...")

        # 读取启动信息
        restart_info = {}
        if self.restart_info_file.exists():
            with open(self.restart_info_file, encoding='utf-8') as f:
                restart_info = json.load(f)

        # 使用 AI 分析
        prompt = get_restart_strategy_prompt(
            timestamp=datetime.now().isoformat(),
            error_type=error_type,
            error_message=error_message,
            traceback=traceback,
            command=restart_info.get('command', 'unknown'),
            args=restart_info.get('args', []),
            args_analysis="",
            restart_count=restart_info.get('restart_count', 0),
            working_directory=restart_info.get('working_directory', 'unknown')
        )

        output = self.ai.call_ai(prompt)

        if output:
            try:
                # 解析 JSON
                if output.startswith('```'):
                    lines = output.split('\n')
                    if lines[0].startswith('```'):
                        output = '\n'.join(lines[1:])
                    if output.endswith('```'):
                        output = output[:-3]
                    output = output.strip()

                strategy = json.loads(output)

                if strategy.get('should_restart'):
                    restart_strategy = strategy.get('restart_strategy', 'immediate')

                    if restart_strategy == 'manual':
                        print(f"[!] 需要人工干预: {strategy.get('recommendation', 'unknown')}")
                        return False

                    # 执行重启
                    print(f"[ℹ️] 重启策略: {restart_strategy}")
                    print(f"[ℹ️] 原因: {strategy.get('reason', 'unknown')}")

                    # 延迟重启
                    if restart_strategy == 'delayed':
                        delay = strategy.get('delay_seconds', 5)
                        print(f"[ℹ️] {delay} 秒后重启...")
                        time.sleep(delay)

                    # 修改参数重启
                    command = restart_info.get('command', sys.executable)
                    args = restart_info.get('args', [])

                    if restart_strategy == 'modified':
                        modified_args = strategy.get('modified_args', [])
                        if modified_args:
                            args.extend(modified_args)
                            print(f"[ℹ️] 使用修改后的参数: {' '.join(modified_args)}")

                    print(f"[ℹ️] 正在重启: {command} {' '.join(args)}")

                    # 替换当前进程
                    os.execvp(command, [command] + args)

                else:
                    print(f"[ℹ️] 不建议重启: {strategy.get('reason', 'unknown')}")
                    return False

            except json.JSONDecodeError as e:
                print(f"[!] 解析重启策略失败: {e}")
                return False

        return False

    def _get_restart_count(self) -> int:
        """获取重启次数"""
        if self.restart_history_file.exists():
            try:
                with open(self.restart_history_file, encoding='utf-8') as f:
                    history = json.load(f)
                    return len(history)
            except Exception:
                pass
        return 0


class DevBotCore:
    """Dev-Bot 核心类 - 统一管理所有功能"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()

        # 初始化日志目录
        log_dir = self.project_root / ".ai-logs"

        # 初始化组件
        self.ai = AIOrchestrator(log_dir=log_dir)
        self.repl = REPLManager(project_root=self.project_root)
        self.spec = SpecManager(self.project_root)
        self.fixer = AutoFixer(self.ai)
        self.restarter = AutoRestarter(self.ai, self.project_root)

        # 动态提示词修改内容管理
        self.prompt_modification = None  # 对提示词的修改内容
        self.prompt_modification_type = None  # 修改类型
        self.prompt_modification_context = None  # 修改的上下文

    def run(self, spec_file: Optional[str] = None):
        """运行 Dev-Bot"""
        print("="*60)
        print("Dev-Bot 核心 - AI 驱动的 Spec 开发系统")
        print("="*60)
        print()

        # 记录启动
        self.restarter.record_startup(sys.executable, sys.argv)

        # 启动 REPL
        self.repl.start()
        print("[✅] REPL 模式已启动")

        # 加载 Spec
        spec_validation = self.spec.validate_specs()
        print(f"[ℹ️] Spec 验证: {spec_validation['valid']}/{spec_validation['total']} 有效")

        if spec_validation['issues']:
            print("[!] Spec 问题:")
            for issue in spec_validation['issues']:
                print(f"  - {issue}")

        print()

        # 主循环
        session_num = 0
        while True:
            session_num += 1

            print(f">>> 会话 #{session_num} <<<")
            print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            # 获取用户输入
            user_inputs = self.repl.get_recent_inputs(5)
            if user_inputs:
                print("[ℹ️] 最近的用户输入:")
                for inp in user_inputs:
                    print(f"  - {inp}")
                print()

            # 加载 Spec 内容
            spec_content = ""
            if spec_file and Path(spec_file).exists():
                with open(spec_file, encoding='utf-8') as f:
                    spec_content = f.read()

            # 构建提示词
            prompt = self._build_prompt(spec_content, user_inputs)

            # 调用 AI
            output = self.ai.call_and_log(prompt, session_num)

            if output:
                print("[ℹ️] AI 输出:")
                print(output)
                print()

                # 使用 AI 分析并决策
                decision = self._analyze_and_decide(output)

                if decision:
                    action = decision.get('action', 'none')
                    print(f"[ℹ️] AI 决策: {action}")

                    # 执行动作
                    self._execute_action(action, decision)

            # 短暂延迟
            time.sleep(1)

            print("-"*60)
            print()

    def _build_prompt(self, spec_content: str, user_inputs: List[str]) -> str:
        """构建提示词"""
        # 先构建基础提示词（包含 Spec 和用户输入）
        prompt = "你是 Dev-Bot 的 AI 开发助手。"

        if spec_content:
            prompt += f"\n\n## Spec 内容\n{spec_content}\n"

        if user_inputs:
            prompt += f"\n\n## 用户输入\n{chr(10).join(f'- {inp}' for inp in user_inputs)}\n"

        prompt += """
        
## 任务

根据 Spec 和用户输入，完成开发工作：

1. 理解 Spec 中的需求
2. 分析用户输入的指令
3. 编写/修改代码实现功能
4. 确保代码质量
5. 运行测试验证

## 输出格式

请直接输出你的工作内容，包括：
- 代码更改（使用代码块）
- 测试结果
- 遇到的问题
- 下一步建议

不需要使用特定的格式标记，自然输出即可。
"""

        # 如果有提示词修改内容，应用到基础提示词上
        if self.prompt_modification:
            prompt += f"\n\n## 修改或补充要求\n{self.prompt_modification}\n"

            # 如果有修改的上下文，也添加进去
            if self.prompt_modification_context:
                prompt += f"\n## 上下文\n{self.prompt_modification_context}\n"

        return prompt

    def _analyze_and_decide(self, ai_output: str) -> Optional[Dict[str, Any]]:
        """使用 AI 分析并决策"""

        # 获取质量报告
        quality_report = self._get_quality_report()

        # 获取用户输入
        user_inputs = self.repl.get_inputs()
        user_inputs_text = "\n".join(f"- {inp}" for inp in user_inputs) if user_inputs else "无"

        # 获取 Spec 和代码一致性分析
        spec_consistency = self._get_spec_code_consistency()

        # 构建决策提示词
        prompt = get_decision_prompt(
            quality_report=quality_report,
            spec_code_consistency=spec_consistency,
            user_inputs_text=user_inputs_text,
            ai_output=ai_output
        )

        # 调用 AI 进行决策
        output = self.ai.call_ai(prompt)

        if output:
            try:
                decision = json.loads(output)

                # 处理 ask_user_spec_or_code 动作
                if decision.get('action') == 'ask_user_spec_or_code':
                    user_question = decision.get('user_question', '')
                    if user_question:
                        self._ask_user_via_repl(user_question)
                        # 修改动作为 continue，不阻塞
                        decision['action'] = 'continue'
                        decision['reason'] = '已通过 REPL 询问用户，继续执行'

                # 更新提示词修改内容
                next_prompt = decision.get('next_prompt')
                if next_prompt:
                    self.prompt_modification = next_prompt
                    self.prompt_modification_type = decision.get('next_prompt_type', 'custom')
                    self.prompt_modification_context = decision.get('next_context', '')
                    print(f"[ℹ️] 已生成提示词修改 (类型: {self.prompt_modification_type})")
                else:
                    # 如果没有提示词修改，清空修改内容
                    self.prompt_modification = None
                    self.prompt_modification_type = None
                    self.prompt_modification_context = None

                return decision
            except json.JSONDecodeError:
                print(f"[!] AI 决策结果解析失败: {output}")
                # 降级到简单规则
                return self._fallback_decision(ai_output)
        else:
            # AI 调用失败，降级到简单规则
            return self._fallback_decision(ai_output)

    def _get_quality_report(self) -> str:
        """获取质量报告"""
        # 简化版质量报告
        return """
## 代码质量
- 语法检查: 未运行
- 类型检查: 未运行
- 测试覆盖率: 未运行

## Spec 质量
- Spec 完整性: 待检查
- Spec 有效性: 待检查
"""

    def _get_spec_code_consistency(self) -> str:
        """获取 Spec 和代码一致性分析"""
        try:
            # 获取代码摘要
            code_summary = self._get_code_summary()

            # 分析一致性
            consistency = self.spec.analyze_spec_code_consistency(
                code_summary=code_summary,
                ai_orchestrator=self.ai,
                tech_stack=self._get_tech_stack()
            )

            if consistency.get('is_consistent'):
                return f"Spec 和代码一致 (一致性分数: {consistency.get('consistency_score', 1.0)})"
            else:
                issues_text = "\n".join(
                    f"- {issue.get('description', '')} ({issue.get('severity', 'unknown')})"
                    for issue in consistency.get('issues', [])
                )
                return f"Spec 和代码不一致:\n{issues_text}"
        except Exception as e:
            print(f"[!] Spec 和代码一致性分析失败: {e}")
            return "无法分析 Spec 和代码一致性"

    def _get_code_summary(self) -> str:
        """获取代码摘要"""
        # 简化版代码摘要
        return """
## 主要模块
- AI 协调器 (AIOrchestrator)
- REPL 管理器 (REPLManager)
- Spec 管理器 (SpecManager)
- 自动修复器 (AutoFixer)
- 自动重启器 (AutoRestarter)

## 主要功能
- AI 驱动的开发决策
- 非阻塞用户输入
- Spec 驱动开发
- 自动错误修复
- 智能重启
"""

    def _get_tech_stack(self) -> str:
        """获取技术栈信息"""
        return "Python 3.14+, subprocess, threading, JSON"

    def _fallback_decision(self, ai_output: str) -> Dict[str, Any]:
        """降级决策 - 简单规则匹配"""
        if '错误' in ai_output or 'error' in ai_output.lower():
            return {
                'action': 'fix_errors',
                'reason': '检测到错误'
            }
        elif '完成' in ai_output or 'done' in ai_output.lower():
            return {
                'action': 'stop',
                'reason': '任务已完成'
            }
        elif '测试' in ai_output or 'test' in ai_output.lower():
            return {
                'action': 'run_tests',
                'reason': '需要运行测试'
            }
        else:
            return {
                'action': 'continue',
                'reason': '继续下一轮'
            }

    def _ask_user_via_repl(self, question: str):
        """通过 REPL 询问用户（非阻塞）"""
        try:
            with open(self.repl.input_file, 'a', encoding='utf-8') as f:
                f.write(f"\n# Dev-Bot 问题 ({datetime.now().isoformat()})\n")
                f.write(f"{question}\n")
                f.write("# 请选择:\n")
                f.write("# 1. 更新 Spec\n")
                f.write("# 2. 修改代码\n")
                f.write("# 3. 两者都修改\n")
                f.write("# 4. 忽略\n")
                f.write("# 输入你的选择: ")
            print(f"[ℹ️] 已通过 REPL 询问用户: {question}")
        except Exception as e:
            print(f"[!] 写入 REPL 输入失败: {e}")

    def _execute_action(self, action: str, decision: Dict[str, Any]):
        """执行动作"""
        if action == 'fix_errors':
            # 自动修复
            errors = ['语法错误', '类型错误']  # 示例
            self.fixer.fix_errors(errors)
        elif action == 'run_tests':
            # 运行测试
            print("[ℹ️] 运行测试...")
            result = subprocess.run(['pytest', '-v'], capture_output=True, text=True)
            if result.returncode == 0:
                print("[✅] 测试通过")
            else:
                print("[!] 测试失败")
                print(result.stdout)
        elif action == 'git_commit':
            # Git 提交
            print("[ℹ️] Git 提交...")
            result = subprocess.run(['git', 'commit', '-m', decision.get('reason', '自动提交')], capture_output=True, text=True)
            if result.returncode == 0:
                print("[✅] Git 提交成功")
            else:
                print("[!] Git 提交失败")
                print(result.stderr)
        elif action == 'update_spec':
            # 更新 Spec
            print("[ℹ️] 更新 Spec...")
            print(f"[ℹ️] 建议: {decision.get('reason', '')}")
        elif action == 'stop':
            print("[✅] 任务完成，退出")
            self.repl.stop()
            sys.exit(0)
        elif action == 'continue' or action == 'none':
            print("[ℹ️] 继续下一轮...")
        elif action == 'ask_user_spec_or_code':
            # 已经在 _analyze_and_decide 中处理，转换为 continue
            print("[ℹ️] 继续下一轮...")
        else:
            print(f"[ℹ️] 未知动作: {action}，继续下一轮...")

    def stop(self):
        """停止 Dev-Bot"""
        self.repl.stop()


# 便捷函数
def create_bot(project_root: Optional[Path] = None) -> DevBotCore:
    """创建 Dev-Bot 实例"""
    return DevBotCore(project_root)
