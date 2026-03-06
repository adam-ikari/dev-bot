#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dev-Bot 自我迭代系统

核心能力：
1. 自我观察 - 收集系统运行数据
2. 自我分析 - 分析数据，识别问题
3. 自我规划 - 制定改进计划
4. 自我执行 - 执行改进
5. 自我验证 - 验证改进效果
6. 自我学习 - 从经验中学习
"""

import asyncio
import json
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from dev_bot.core import get_core
from dev_bot.output_router import get_output_router, OutputSource, LogLevel
from dev_bot.ai_dialogue import get_dialogue_manager
from dev_bot.ai_evolution_system import AIDecisionSystem, DecisionType
from dev_bot.dialogue_integrator import DialogueIntegrator


class IterationPhase(Enum):
    """迭代阶段"""
    OBSERVE = "observe"       # 观察
    ANALYZE = "analyze"       # 分析
    PLAN = "plan"             # 规划
    EXECUTE = "execute"       # 执行
    VERIFY = "verify"         # 验证
    LEARN = "learn"           # 学习


class ImprovementType(Enum):
    """改进类型"""
    CODE_QUALITY = "code_quality"      # 代码质量
    PERFORMANCE = "performance"         # 性能
    ARCHITECTURE = "architecture"       # 架构
    DOCUMENTATION = "documentation"     # 文档
    TESTING = "testing"                # 测试
    PROMPT_OPTIMIZATION = "prompt"     # 提示词优化
    BUG_FIX = "bug_fix"                # 错误修复
    FEATURE_ENHANCEMENT = "feature"    # 功能增强


@dataclass
class SystemMetric:
    """系统指标"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    test_pass_rate: float
    code_coverage: float
    error_count: int
    performance_score: float
    user_satisfaction: float


@dataclass
class ImprovementSuggestion:
    """改进建议"""
    type: ImprovementType
    title: str
    description: str
    priority: int
    estimated_effort: int
    expected_impact: int
    implementation_plan: str
    verification_criteria: str


@dataclass
class IterationRecord:
    """迭代记录"""
    iteration_id: str
    phase: IterationPhase
    timestamp: float
    metrics: SystemMetric
    analysis: Dict[str, Any]
    suggestions: List[ImprovementSuggestion]
    execution_result: Dict[str, Any]
    verification_result: Dict[str, Any]
    lessons_learned: List[str]


class SelfIterationSystem:
    """自我迭代系统
    
    完整的自我迭代循环：
    观察 → 分析 → 规划 → 执行 → 验证 → 学习
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.core = get_core()
        self.output_router = get_output_router()
        self.dialogue_manager = get_dialogue_manager()
        self.decision_system = AIDecisionSystem(project_root)
        self.dialogue_integrator = DialogueIntegrator()

        # 迭代数据目录
        self.iteration_dir = project_root / ".dev-bot-evolution"
        self.iteration_dir.mkdir(exist_ok=True)

        # 迭代历史
        self.history_file = self.iteration_dir / "iteration_history.json"
        self.iteration_history: List[IterationRecord] = self._load_history()

        # 当前迭代
        self.current_iteration: Optional[IterationRecord] = None
        self.iteration_counter = len(self.iteration_history)

        # 经验库
        self.experience_file = self.iteration_dir / "experience.json"
        self.experience: Dict[str, Any] = self._load_experience()

        # 运行标志
        self.is_running = False

    def _load_history(self) -> List[IterationRecord]:
        """加载迭代历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, encoding='utf-8') as f:
                    data = json.load(f)
                    return [IterationRecord(**record) for record in data]
            except Exception as e:
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.WARNING,
                    f"加载迭代历史失败: {str(e)}"
                )
        return []

    def _load_experience(self) -> Dict[str, Any]:
        """加载经验库"""
        if self.experience_file.exists():
            try:
                with open(self.experience_file, encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                await self.output_router.emit(
                    OutputSource.SYSTEM,
                    LogLevel.WARNING,
                    f"加载经验库失败: {str(e)}"
                )
        return {
            "successful_improvements": [],
            "failed_improvements": [],
            "patterns": {},
            "best_practices": []
        }

    def _save_history(self):
        """保存迭代历史"""
        data = [
            {
                "iteration_id": r.iteration_id,
                "phase": r.phase.value,
                "timestamp": r.timestamp,
                "metrics": r.metrics.__dict__,
                "analysis": r.analysis,
                "suggestions": [s.__dict__ for s in r.suggestions],
                "execution_result": r.execution_result,
                "verification_result": r.verification_result,
                "lessons_learned": r.lessons_learned
            }
            for r in self.iteration_history
        ]
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _save_experience(self):
        """保存经验库"""
        with open(self.experience_file, 'w', encoding='utf-8') as f:
            json.dump(self.experience, f, indent=2, ensure_ascii=False)

    async def observe(self) -> SystemMetric:
        """观察阶段 - 收集系统指标"""
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            "[自我迭代] 开始观察阶段..."
        )

        # 收集各项指标
        metrics = SystemMetric(
            timestamp=time.time(),
            cpu_usage=await self._get_cpu_usage(),
            memory_usage=await self._get_memory_usage(),
            test_pass_rate=await self._get_test_pass_rate(),
            code_coverage=await self._get_code_coverage(),
            error_count=await self._get_error_count(),
            performance_score=await self._get_performance_score(),
            user_satisfaction=await self._get_user_satisfaction()
        )

        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] 指标收集完成: "
            f"测试通过率={metrics.test_pass_rate:.2%}, "
            f"代码覆盖率={metrics.code_coverage:.2%}, "
            f"性能评分={metrics.performance_score:.2f}"
        )

        return metrics

    async def _get_cpu_usage(self) -> float:
        """获取 CPU 使用率"""
        try:
            result = await asyncio.create_subprocess_exec(
                "ps",
                "-p",
                str(subprocess.getpid()),
                "-o",
                "%cpu",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            if stdout:
                return float(stdout.decode().strip().split()[-1])
        except Exception:
            pass
        return 0.0

    async def _get_memory_usage(self) -> float:
        """获取内存使用率"""
        try:
            result = await asyncio.create_subprocess_exec(
                "ps",
                "-p",
                str(subprocess.getpid()),
                "-o",
                "%mem",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            if stdout:
                return float(stdout.decode().strip().split()[-1])
        except Exception:
            pass
        return 0.0

    async def _get_test_pass_rate(self) -> float:
        """获取测试通过率"""
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
            stdout, _ = await result.communicate()
            output = stdout.decode()
            
            # 解析 pytest 输出
            if "passed" in output:
                parts = output.split()
                for part in parts:
                    if "passed" in part:
                        passed = int(part.split()[0])
                        total = passed
                        for p in parts:
                            if "failed" in p:
                                total += int(p.split()[0])
                        return passed / total if total > 0 else 0.0
        except Exception:
            pass
        return 0.0

    async def _get_code_coverage(self) -> float:
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
            
            # 解析覆盖率输出
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

    async def _get_error_count(self) -> int:
        """获取错误数量"""
        error_dir = self.project_root / ".error-logs"
        if error_dir.exists():
            return len(list(error_dir.glob("*.json")))
        return 0

    async def _get_performance_score(self) -> float:
        """获取性能评分"""
        # 基于多个因素计算性能评分
        cpu = await self._get_cpu_usage()
        memory = await self._get_memory_usage()
        
        # 简单评分：CPU 和内存使用率越低，分数越高
        score = 10.0 - (cpu / 10.0) - (memory / 10.0)
        return max(0.0, min(10.0, score))

    async def _get_user_satisfaction(self) -> float:
        """获取用户满意度"""
        # 从对话历史和用户反馈中计算
        # 这里简化处理，返回一个默认值
        return 8.0

    async def analyze(self, metrics: SystemMetric) -> Dict[str, Any]:
        """分析阶段 - 分析指标，识别问题"""
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            "[自我迭代] 开始分析阶段..."
        )

        # 使用 AI 分析指标
        prompt = f"""你是 Dev-Bot 的自我分析系统。

当前系统指标：
- CPU 使用率: {metrics.cpu_usage}%
- 内存使用率: {metrics.memory_usage}%
- 测试通过率: {metrics.test_pass_rate:.2%}
- 代码覆盖率: {metrics.code_coverage:.2%}
- 错误数量: {metrics.error_count}
- 性能评分: {metrics.performance_score:.2f}/10
- 用户满意度: {metrics.user_satisfaction:.2f}/10

请分析：
1. 系统当前的主要问题是什么？
2. 哪些指标需要改进？
3. 改进的优先级如何？
4. 有哪些明显的模式？

返回 JSON 格式：
{{
    "problems": ["问题1", "问题2"],
    "priorities": {{"问题1": 1, "问题2": 2}},
    "patterns": ["模式1", "模式2"],
    "overall_assessment": "整体评估"
}}"""

        result = await self.core.call_iflow(prompt, timeout=120)

        if result["success"]:
            analysis = json.loads(result["output"])
        else:
            analysis = {
                "problems": [],
                "priorities": {},
                "patterns": [],
                "overall_assessment": "分析失败"
            }

        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] 分析完成，发现 {len(analysis.get('problems', []))} 个问题"
        )

        return analysis

    async def plan(
        self,
        metrics: SystemMetric,
        analysis: Dict[str, Any]
    ) -> List[ImprovementSuggestion]:
        """规划阶段 - 生成改进建议"""
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            "[自我迭代] 开始规划阶段..."
        )

        # 使用 AI 生成改进建议
        prompt = f"""你是 Dev-Bot 的改进规划系统。

分析结果：
{json.dumps(analysis, ensure_ascii=False, indent=2)}

系统指标：
{json.dumps(metrics.__dict__, ensure_ascii=False, indent=2)}

请为每个问题生成改进建议，包括：
1. 改进类型（code_quality, performance, architecture, documentation, testing, prompt, bug_fix, feature）
2. 改进标题
3. 详细描述
4. 优先级（1-5，5最高）
5. 预估工作量（1-10，10最大）
6. 预期影响（1-10，10最大）
7. 实施计划（具体步骤）
8. 验证标准（如何验证改进成功）

返回 JSON 格式：
{{
    "suggestions": [
        {{
            "type": "改进类型",
            "title": "标题",
            "description": "描述",
            "priority": 1-5,
            "estimated_effort": 1-10,
            "expected_impact": 1-10,
            "implementation_plan": "计划",
            "verification_criteria": "标准"
        }}
    ]
}}"""

        result = await self.core.call_iflow(prompt, timeout=180)

        if result["success"]:
            data = json.loads(result["output"])
            suggestions = [
                ImprovementSuggestion(**s) for s in data.get("suggestions", [])
            ]
        else:
            suggestions = []

        # 按优先级排序
        suggestions.sort(key=lambda s: s.priority, reverse=True)

        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] 规划完成，生成 {len(suggestions)} 个改进建议"
        )

        return suggestions

    async def execute(
        self,
        suggestions: List[ImprovementSuggestion]
    ) -> Dict[str, Any]:
        """执行阶段 - 执行改进"""
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            "[自我迭代] 开始执行阶段..."
        )

        results = {}

        # 创建 AI 对话来讨论和执行改进
        dialogue_id = self.dialogue_manager.create_dialogue(
            participants=["analyzer", "developer", "tester", "reviewer"],
            topic="Dev-Bot 自我改进实施",
            mode="group"
        )

        # 添加改进建议到对话
        for suggestion in suggestions[:3]:  # 先执行前3个高优先级改进
            prompt = f"""改进建议：

类型: {suggestion.type.value}
标题: {suggestion.title}
描述: {suggestion.description}
优先级: {suggestion.priority}
预估工作量: {suggestion.estimated_effort}
预期影响: {suggestion.expected_impact}

实施计划:
{suggestion.implementation_plan}

请讨论并决定如何实施这个改进。"""

            self.dialogue_manager.add_message(
                dialogue_id,
                "coordinator",
                prompt
            )

        # 运行对话
        await self.dialogue_manager.start_autonomous_dialogue(
            dialogue_id,
            max_duration=300
        )

        # 获取对话结果
        dialogue = self.dialogue_manager.get_dialogue(dialogue_id)
        results["dialogue"] = dialogue.to_dict()

        # 根据对话结果执行改进
        for suggestion in suggestions[:3]:
            result = await self._execute_improvement(suggestion)
            results[suggestion.title] = result

        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] 执行完成，处理了 {min(3, len(suggestions))} 个改进"
        )

        return results

    async def _execute_improvement(
        self,
        suggestion: ImprovementSuggestion
    ) -> Dict[str, Any]:
        """执行单个改进"""
        result = {
            "success": False,
            "changes": [],
            "errors": []
        }

        try:
            # 解析实施计划
            plan_steps = suggestion.implementation_plan.split("\n")

            for step in plan_steps:
                step = step.strip()
                if not step or step.startswith("-"):
                    continue

                # 使用 iflow 执行改进
                step_result = await self.core.execute(step)

                if step_result["success"]:
                    result["changes"].append(step)
                else:
                    result["errors"].append(f"步骤失败: {step}")

            result["success"] = len(result["errors"]) == 0

        except Exception as e:
            result["errors"].append(f"执行异常: {str(e)}")

        return result

    async def verify(
        self,
        execution_result: Dict[str, Any],
        baseline_metrics: SystemMetric
    ) -> Dict[str, Any]:
        """验证阶段 - 验证改进效果"""
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            "[自我迭代] 开始验证阶段..."
        )

        # 收集新的指标
        new_metrics = await self.observe()

        # 比较指标变化
        comparison = {
            "test_pass_rate_delta": new_metrics.test_pass_rate - baseline_metrics.test_pass_rate,
            "code_coverage_delta": new_metrics.code_coverage - baseline_metrics.code_coverage,
            "performance_score_delta": new_metrics.performance_score - baseline_metrics.performance_score,
            "error_count_delta": baseline_metrics.error_count - new_metrics.error_count,
            "user_satisfaction_delta": new_metrics.user_satisfaction - baseline_metrics.user_satisfaction
        }

        # 判断改进是否成功
        success = (
            comparison["test_pass_rate_delta"] >= 0 and
            comparison["code_coverage_delta"] >= 0 and
            comparison["performance_score_delta"] >= 0
        )

        verification_result = {
            "success": success,
            "baseline_metrics": baseline_metrics.__dict__,
            "new_metrics": new_metrics.__dict__,
            "comparison": comparison,
            "overall_improvement": sum(comparison.values())
        }

        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO if success else LogLevel.WARNING,
            f"[自我迭代] 验证完成，改进{'成功' if success else '失败'}"
        )

        return verification_result

    async def learn(
        self,
        iteration_record: IterationRecord
    ) -> List[str]:
        """学习阶段 - 从经验中学习"""
        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            "[自我迭代] 开始学习阶段..."
        )

        lessons = []

        # 分析成功和失败的改进
        for suggestion in iteration_record.suggestions:
            result = iteration_record.execution_result.get(suggestion.title, {})
            
            if result.get("success"):
                # 记录成功经验
                lesson = f"成功: {suggestion.title} - {suggestion.description}"
                lessons.append(lesson)
                
                self.experience["successful_improvements"].append({
                    "type": suggestion.type.value,
                    "title": suggestion.title,
                    "description": suggestion.description,
                    "timestamp": time.time()
                })
            else:
                # 记录失败经验
                lesson = f"失败: {suggestion.title} - {result.get('errors', [])}"
                lessons.append(lesson)
                
                self.experience["failed_improvements"].append({
                    "type": suggestion.type.value,
                    "title": suggestion.title,
                    "description": suggestion.description,
                    "errors": result.get("errors", []),
                    "timestamp": time.time()
                })

        # 识别模式
        successful_types = [
            imp["type"]
            for imp in self.experience["successful_improvements"]
        ]
        if successful_types:
            from collections import Counter
            type_counts = Counter(successful_types)
            self.experience["patterns"]["successful_types"] = type_counts.most_common()

        # 保存经验
        self._save_experience()

        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] 学习完成，总结 {len(lessons)} 条经验"
        )

        return lessons

    async def run_iteration(self) -> IterationRecord:
        """运行一次完整的迭代循环"""
        self.iteration_counter += 1
        iteration_id = f"iteration_{self.iteration_counter}_{int(time.time())}"

        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] 开始迭代 #{self.iteration_counter}: {iteration_id}"
        )

        # 观察阶段
        metrics = await self.observe()

        # 分析阶段
        analysis = await self.analyze(metrics)

        # 规划阶段
        suggestions = await self.plan(metrics, analysis)

        # 执行阶段
        execution_result = await self.execute(suggestions)

        # 验证阶段
        verification_result = await self.verify(execution_result, metrics)

        # 学习阶段
        iteration_record = IterationRecord(
            iteration_id=iteration_id,
            phase=IterationPhase.LEARN,
            timestamp=time.time(),
            metrics=metrics,
            analysis=analysis,
            suggestions=suggestions,
            execution_result=execution_result,
            verification_result=verification_result,
            lessons_learned=[]
        )

        lessons = await self.learn(iteration_record)
        iteration_record.lessons_learned = lessons

        # 保存迭代记录
        self.iteration_history.append(iteration_record)
        self._save_history()

        await self.output_router.emit(
            OutputSource.SYSTEM,
            LogLevel.INFO,
            f"[自我迭代] 迭代 #{self.iteration_counter} 完成"
        )

        return iteration_record

    async def start_continuous_iteration(self, interval: int = 3600):
        """启动连续迭代模式"""
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
                await asyncio.sleep(60)  # 出错后等待1分钟再重试

    def stop(self):
        """停止连续迭代"""
        self.is_running = False


# 全局自我迭代系统实例
_global_self_iteration: Optional[SelfIterationSystem] = None


def get_self_iteration_system(project_root: Path) -> SelfIterationSystem:
    """获取全局自我迭代系统实例"""
    global _global_self_iteration
    
    if _global_self_iteration is None:
        _global_self_iteration = SelfIterationSystem(project_root)
    
    return _global_self_iteration
