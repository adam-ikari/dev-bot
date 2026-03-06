#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dev-Bot 极简自我迭代系统

核心原则：
- 极简设计：只依赖 AI 能力
- AI 自主：AI 决定做什么、怎么做
- 单次迭代：每次迭代独立，AI 根据当前状态决策

迭代循环：
观察 → AI 分析决策 → AI 执行 → 验证
"""

import asyncio
import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dev_bot.core import get_core
from dev_bot.output_router import get_output_router, OutputSource, LogLevel


@dataclass
class IterationContext:
    """迭代上下文"""
    iteration_id: str
    timestamp: float
    test_results: Dict[str, Any]
    code_coverage: float
    error_count: int
    recent_changes: List[str]
    git_status: Dict[str, Any]
    system_metrics: Dict[str, Any]


class SimpleSelfIteration:
    """极简自我迭代系统
    
    完全依赖 AI 能力，让 AI 自主分析和改进
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.core = get_core()
        self.output_router = get_output_router()
        
        # 迭代数据目录
        self.iteration_dir = project_root / ".dev-bot-evolution"
        self.iteration_dir.mkdir(exist_ok=True)
        
        # 迭代日志
        self.log_file = self.iteration_dir / "iteration_log.json"
        self.iteration_log: List[Dict] = self._load_log()
        
        # 运行标志
        self.is_running = False

    def _load_log(self) -> List[Dict]:
        """加载迭代日志"""
        if self.log_file.exists():
            try:
                with open(self.log_file, encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_log(self):
        """保存迭代日志"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.iteration_log, f, indent=2, ensure_ascii=False)

    async def _collect_context(self) -> IterationContext:
        """收集当前上下文"""
        iteration_id = f"iter_{len(self.iteration_log) + 1}_{int(time.time())}"
        
        # 获取测试结果
        test_results = await self._run_tests()
        
        # 获取代码覆盖率
        coverage = await self._get_coverage()
        
        # 获取错误数量
        error_count = len(list((self.project_root / ".error-logs").glob("*.json")))
        
        # 获取最近的变更
        recent_changes = await self._get_recent_changes()
        
        # 获取 Git 状态
        git_status = await self._get_git_status()
        
        # 获取系统指标
        system_metrics = await self._get_system_metrics()

        return IterationContext(
            iteration_id=iteration_id,
            timestamp=time.time(),
            test_results=test_results,
            code_coverage=coverage,
            error_count=error_count,
            recent_changes=recent_changes,
            git_status=git_status,
            system_metrics=system_metrics
        )

    async def _run_tests(self) -> Dict[str, Any]:
        """运行测试"""
        try:
            result = await asyncio.create_subprocess_exec(
                "uv",
                "run",
                "pytest",
                "--tb=no",
                "-q",
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return {
                "output": stdout.decode(),
                "stderr": stderr.decode(),
                "returncode": result.returncode
            }
        except Exception as e:
            return {"error": str(e), "returncode": -1}

    async def _get_coverage(self) -> float:
        """获取代码覆盖率"""
        try:
            result = await asyncio.create_subprocess_exec(
                "uv",
                "run",
                "pytest",
                "--cov=dev_bot",
                "--cov-report=term-missing",
                "--tb=no",
                "-q",
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            output = stdout.decode()
            
            if "TOTAL" in output:
                lines = output.split("\n")
                for line in lines:
                    if "TOTAL" in line:
                        parts = line.split()
                        for part in parts:
                            if "%" in part:
                                return float(part.replace("%", ""))
        except Exception:
            pass
        return 0.0

    async def _get_recent_changes(self) -> List[str]:
        """获取最近的变更"""
        try:
            result = await asyncio.create_subprocess_exec(
                "git",
                "log",
                "--oneline",
                "-10",
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            return stdout.decode().strip().split("\n")
        except Exception:
            return []

    async def _get_git_status(self) -> Dict[str, Any]:
        """获取 Git 状态"""
        try:
            result = await asyncio.create_subprocess_exec(
                "git",
                "status",
                "--porcelain",
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            status_lines = stdout.decode().strip().split("\n")
            
            modified = [line for line in status_lines if line.startswith(" M")]
            added = [line for line in status_lines if line.startswith("??")]
            deleted = [line for line in status_lines if line.startswith(" D")]
            
            return {
                "modified": len(modified),
                "added": len(added),
                "deleted": len(deleted),
                "dirty": len(status_lines) > 0
            }
        except Exception:
            return {"dirty": False}

    async def _get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            result = await asyncio.create_subprocess_exec(
                "ps",
                "-p",
                str(subprocess.getpid()),
                "-o",
                "%cpu,%mem,vsz,rss",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            if stdout:
                parts = stdout.decode().strip().split()
                if len(parts) >= 4:
                    return {
                        "cpu": float(parts[-4]),
                        "memory": float(parts[-3]),
                        "vsz": int(parts[-2]),
                        "rss": int(parts[-1])
                    }
        except Exception:
            pass
        return {}

    async def ai_analyze_and_decide(self, context: IterationContext) -> Dict[str, Any]:
        """AI 分析当前状态并决定改进方向"""
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] {context.iteration_id}: AI 开始分析..."
        )

        # 构建分析提示词
        prompt = f"""你是 Dev-Bot 的自我改进系统，负责分析和改进代码。

## 当前迭代信息
- 迭代 ID: {context.iteration_id}
- 时间: {datetime.fromtimestamp(context.timestamp).isoformat()}

## 系统状态
- 测试结果: {context.test_results.get('returncode', -1)}
- 代码覆盖率: {context.code_coverage:.2f}%
- 错误数量: {context.error_count}
- CPU 使用率: {context.system_metrics.get('cpu', 0)}%
- 内存使用率: {context.system_metrics.get('memory', 0)}%

## Git 状态
- 修改文件: {context.git_status.get('modified', 0)}
- 新增文件: {context.git_status.get('added', 0)}
- 工作区是否干净: {'否' if context.git_status.get('dirty') else '是'}

## 最近变更
{chr(10).join(f"- {c}" for c in context.recent_changes[:5])}

## 任务
请分析当前状态，并决定：
1. 当前最需要改进的问题是什么？
2. 应该采取什么行动？
3. 具体的实施步骤是什么？

## 返回格式
返回 JSON 格式：
{{
    "analysis": "当前状态分析",
    "problem": "主要问题",
    "action": "采取的行动（如：修复测试、优化代码、添加功能、重构代码等）",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "expected_outcome": "预期结果"
}}

只返回 JSON，不要有其他内容。"""

        # 调用 AI 分析
        result = await self.core.call_iflow(prompt, timeout=120)

        if not result["success"]:
            return {
                "analysis": "AI 调用失败",
                "problem": "无法分析",
                "action": "skip",
                "steps": [],
                "expected_outcome": "无"
            }

        # 解析 AI 响应
        try:
            decision = json.loads(result["output"])
        except json.JSONDecodeError:
            return {
                "analysis": "AI 响应格式错误",
                "problem": "无法解析",
                "action": "skip",
                "steps": [],
                "expected_outcome": "无"
            }

        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] {context.iteration_id}: AI 决策 - {decision.get('action', '无')}"
        )

        return decision

    async def ai_execute(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """AI 执行改进"""
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] AI 开始执行: {decision.get('action', '无')}"
        )

        execution_result = {
            "success": False,
            "steps_completed": [],
            "steps_failed": [],
            "changes": [],
            "errors": []
        }

        action = decision.get("action", "skip")
        steps = decision.get("steps", [])

        # 如果是 skip，跳过执行
        if action == "skip":
            execution_result["success"] = True
            return execution_result

        # 使用 AI 执行每个步骤
        for i, step in enumerate(steps, 1):
            try:
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.INFO,
                    f"[自我迭代] 执行步骤 {i}/{len(steps)}: {step}"
                )

                # 构建执行提示词
                execute_prompt = f"""执行以下改进步骤：

步骤 {i}/{len(steps)}: {step}

项目根目录: {self.project_root}

请执行这个步骤。如果是修改代码，请提供具体的代码修改。
如果是运行命令，请只返回要运行的命令。
如果是分析任务，请返回分析结果。

只返回具体的执行内容，不要有解释。"""

                # 调用 AI 执行
                result = await self.core.call_iflow(execute_prompt, timeout=180)

                if result["success"]:
                    output = result["output"].strip()
                    
                    # 判断是命令还是代码修改
                    if output.startswith("```") or output.endswith("```"):
                        # 代码修改
                        execution_result["changes"].append({
                            "step": step,
                            "content": output
                        })
                    elif any(cmd in output for cmd in ["git", "pytest", "uv", "python"]):
                        # 命令
                        await self._execute_command(output)
                        execution_result["changes"].append({
                            "step": step,
                            "command": output
                        })
                    else:
                        # 其他输出
                        execution_result["changes"].append({
                            "step": step,
                            "output": output
                        })
                    
                    execution_result["steps_completed"].append(step)
                else:
                    execution_result["steps_failed"].append(step)
                    execution_result["errors"].append(f"步骤 {i} 执行失败")

            except Exception as e:
                execution_result["steps_failed"].append(step)
                execution_result["errors"].append(f"步骤 {i} 异常: {str(e)}")

        execution_result["success"] = len(execution_result["steps_failed"]) == 0

        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO if execution_result["success"] else LogLevel.WARNING,
            f"[自我迭代] 执行完成: 成功 {len(execution_result['steps_completed'])}/{len(steps)} 步"
        )

        return execution_result

    async def _execute_command(self, command: str):
        """执行命令"""
        try:
            # 提取第一行作为命令
            cmd_line = command.split("\n")[0].strip()
            if not cmd_line:
                return
            
            # 解析命令
            parts = cmd_line.split()
            if not parts:
                return
            
            # 执行命令
            result = await asyncio.create_subprocess_exec(
                *parts,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            await result.communicate()
            
        except Exception as e:
            await self.output_router.emit(
                OutputSource.SYSTEM,
                LogLevel.WARNING,
                f"[自我迭代] 命令执行失败: {str(e)}"
            )

    async def verify(self, context: IterationContext) -> Dict[str, Any]:
        """验证改进效果"""
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] 开始验证..."
        )

        # 重新运行测试
        new_test_results = await self._run_tests()
        
        # 重新获取覆盖率
        new_coverage = await self._get_coverage()
        
        # 重新获取错误数量
        new_error_count = len(list((self.project_root / ".error-logs").glob("*.json")))

        # 比较
        improvements = {
            "test_fixed": context.test_results.get("returncode", -1) != 0 and new_test_results.get("returncode", -1) == 0,
            "coverage_improved": new_coverage > context.code_coverage,
            "errors_reduced": new_error_count < context.error_count,
            "delta_coverage": new_coverage - context.code_coverage,
            "delta_errors": context.error_count - new_error_count
        }

        success = any(improvements.values())

        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO if success else LogLevel.WARNING,
            f"[自我迭代] 验证完成: {'改进成功' if success else '无明显改进'}"
        )

        return {
            "success": success,
            "new_test_results": new_test_results,
            "new_coverage": new_coverage,
            "new_error_count": new_error_count,
            "improvements": improvements
        }

    async def run_iteration(self) -> Dict[str, Any]:
        """运行一次迭代"""
        # 收集上下文
        context = await self._collect_context()
        
        # AI 分析和决策
        decision = await self.ai_analyze_and_decide(context)
        
        # AI 执行
        execution_result = await self.ai_execute(decision)
        
        # 验证
        verification_result = await self.verify(context)
        
        # 记录迭代
        iteration_log = {
            "iteration_id": context.iteration_id,
            "timestamp": context.timestamp,
            "context": {
                "test_results": context.test_results.get("returncode", -1),
                "coverage": context.code_coverage,
                "error_count": context.error_count,
                "git_dirty": context.git_status.get("dirty", False)
            },
            "decision": decision,
            "execution": execution_result,
            "verification": verification_result
        }
        
        self.iteration_log.append(iteration_log)
        self._save_log()
        
        return iteration_log

    async def start_continuous_iteration(self, interval: int = 1800):
        """启动连续迭代（默认30分钟）"""
        self.is_running = True
        
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] 启动连续迭代模式，间隔 {interval} 秒"
        )
        
        while self.is_running:
            try:
                await self.run_iteration()
                await asyncio.sleep(interval)
            except Exception as e:
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.ERROR,
                    f"[自我迭代] 迭代出错: {str(e)}"
                )
                await asyncio.sleep(60)
    
    def stop(self):
        """停止迭代"""
        self.is_running = False


# 全局实例
_global_instance: Optional[SimpleSelfIteration] = None


def get_simple_iteration(project_root: Path) -> SimpleSelfIteration:
    """获取全局实例"""
    global _global_instance
    if _global_instance is None:
        _global_instance = SimpleSelfIteration(project_root)
    return _global_instance