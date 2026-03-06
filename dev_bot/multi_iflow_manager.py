#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多 iFlow 并发调用管理器

支持同时调用多个 iflow 实例，用于：
1. 提高效率（并行处理）
2. 复杂决策（多角度分析）
3. 反思和评估（多观点对比）
"""

import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

from dev_bot.iflow_manager import (
    IFlowManager,
    IFlowMode,
    IFlowCallResult
)


class MultiIFlowStrategy(Enum):
    """多 iFlow 调用策略"""
    PARALLEL = "parallel"  # 并行执行，提高效率
    CONSENSUS = "consensus"  # 共识决策，多角度分析
    EVALUATION = "evaluation"  # 评估对比，多观点对比
    REFLECTION = "reflection"  # 反思改进，自我优化
    DEBATE = "debate"  # 辩论模式，冲突解决


@dataclass
class IForkInstance:
    """iFlow 实例配置"""
    id: str
    role: str  # 角色描述（如：开发者、测试者、审查者）
    perspective: str  # 视角描述（如：代码质量、性能、安全性）
    priority: int = 1  # 优先级（1-10）
    timeout: int = 300  # 超时时间
    mode: IFlowMode = IFlowMode.NORMAL


@dataclass
class MultiIFlowCallResult:
    """多 iFlow 调用结果"""
    strategy: MultiIFlowStrategy
    individual_results: Dict[str, IFlowCallResult] = field(default_factory=dict)
    aggregated_result: str = ""
    consensus_score: float = 0.0
    confidence: float = 0.0
    conflicts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    duration: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "strategy": self.strategy.value,
            "individual_results": {
                k: v.to_dict() for k, v in self.individual_results.items()
            },
            "aggregated_result": self.aggregated_result,
            "consensus_score": self.consensus_score,
            "confidence": self.confidence,
            "conflicts": self.conflicts,
            "recommendations": self.recommendations,
            "duration": self.duration
        }


class MultiIFlowManager:
    """多 iFlow 并发调用管理器
    
    支持同时调用多个 iflow 实例，实现复杂决策和反思
    """
    
    def __init__(
        self,
        iflow_command: str = "iflow",
        default_timeout: int = 300,
        max_retries: int = 3
    ):
        self.iflow_command = iflow_command
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        
        # 创建多个 iflow 管理器实例
        self.managers: Dict[str, IFlowManager] = {}
        
        # 预定义角色配置
        self.predefined_roles = {
            "developer": IForkInstance(
                id="developer",
                role="开发者",
                perspective="实现功能和编写代码",
                priority=10,
                mode=IFlowMode.YOLO
            ),
            "tester": IForkInstance(
                id="tester",
                role="测试者",
                perspective="测试和质量保证",
                priority=8,
                mode=IFlowMode.PLAN
            ),
            "reviewer": IForkInstance(
                id="reviewer",
                role="审查者",
                perspective="代码审查和最佳实践",
                priority=9,
                mode=IFlowMode.THINKING
            ),
            "optimizer": IForkInstance(
                id="optimizer",
                role="优化者",
                perspective="性能优化和资源利用",
                priority=7,
                mode=IFlowMode.PLAN
            ),
            "security": IForkInstance(
                id="security",
                role="安全专家",
                perspective="安全性和漏洞检测",
                priority=9,
                mode=IFlowMode.THINKING
            ),
            "architect": IForkInstance(
                id="architect",
                role="架构师",
                perspective="架构设计和系统规划",
                priority=8,
                mode=IFlowMode.PLAN
            )
        }
        
        print(f"[多iFlow管理器] 初始化完成")
        print(f"[多iFlow管理器] 预定义角色: {len(self.predefined_roles)} 个")
    
    async def call_parallel(
        self,
        prompt: str,
        instances: List[IForkInstance],
        context: Optional[Dict[str, Any]] = None
    ) -> MultiIFlowCallResult:
        """并行调用多个 iflow 实例（提高效率）
        
        Args:
            prompt: 提示词
            instances: iFlow 实例列表
            context: 上下文信息
        
        Returns:
            多 iFlow 调用结果
        """
        import time
        start_time = time.time()
        
        result = MultiIFlowCallResult(strategy=MultiIFlowStrategy.PARALLEL)
        
        # 并行调用所有实例
        tasks = []
        for instance in instances:
            task = self._call_instance(instance, prompt, context)
            tasks.append((instance.id, task))
        
        # 等待所有任务完成
        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )
        
        # 收集结果
        for (instance_id, _), call_result in zip(tasks, results):
            if isinstance(call_result, Exception):
                result.individual_results[instance_id] = IFlowCallResult(
                    success=False,
                    output="",
                    error=str(call_result)
                )
            else:
                result.individual_results[instance_id] = call_result
        
        # 聚合结果
        result.aggregated_result = self._aggregate_parallel_results(result.individual_results)
        result.duration = time.time() - start_time
        
        return result
    
    async def call_consensus(
        self,
        prompt: str,
        instances: List[IForkInstance],
        context: Optional[Dict[str, Any]] = None
    ) -> MultiIFlowCallResult:
        """共识决策（多角度分析）
        
        Args:
            prompt: 提示词
            instances: iFlow 实例列表
            context: 上下文信息
        
        Returns:
            多 iFlow 调用结果
        """
        import time
        start_time = time.time()
        
        result = MultiIFlowCallResult(strategy=MultiIFlowStrategy.CONSENSUS)
        
        # 并行调用
        tasks = []
        for instance in instances:
            # 为共识决策添加角色上下文
            role_context = {
                "role": instance.role,
                "perspective": instance.perspective,
                **(context or {})
            }
            task = self._call_instance(instance, prompt, role_context)
            tasks.append((instance.id, task))
        
        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )
        
        # 收集结果
        for (instance_id, _), call_result in zip(tasks, results):
            if isinstance(call_result, Exception):
                result.individual_results[instance_id] = IFlowCallResult(
                    success=False,
                    output="",
                    error=str(call_result)
                )
            else:
                result.individual_results[instance_id] = call_result
        
        # 分析共识
        result.consensus_score, result.conflicts = self._analyze_consensus(
            result.individual_results,
            instances
        )
        
        # 聚合共识结果
        result.aggregated_result = self._aggregate_consensus_results(
            result.individual_results,
            instances,
            result.consensus_score
        )
        
        result.duration = time.time() - start_time
        
        return result
    
    async def call_evaluation(
        self,
        prompt: str,
        decision: str,
        instances: List[IForkInstance],
        context: Optional[Dict[str, Any]] = None
    ) -> MultiIFlowCallResult:
        """评估对比（多观点对比）
        
        Args:
            prompt: 原始提示词
            decision: 待评估的决策
            instances: iFlow 实例列表
            context: 上下文信息
        
        Returns:
            多 iFlow 调用结果
        """
        import time
        start_time = time.time()
        
        result = MultiIFlowCallResult(strategy=MultiIFlowStrategy.EVALUATION)
        
        # 构建评估提示词
        eval_prompt = f"""请评估以下决策：

原始问题：
{prompt}

待评估的决策：
{decision}

请从你的角度（{context.get('role', '评估者')}，{context.get('perspective', '多角度')}）评估这个决策：
1. 优点
2. 缺点
3. 风险
4. 建议
5. 评分（1-10）
"""
        
        # 并行调用
        tasks = []
        for instance in instances:
            role_context = {
                "role": instance.role,
                "perspective": instance.perspective,
                **(context or {})
            }
            task = self._call_instance(instance, eval_prompt, role_context)
            tasks.append((instance.id, task))
        
        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )
        
        # 收集结果
        for (instance_id, _), call_result in zip(tasks, results):
            if isinstance(call_result, Exception):
                result.individual_results[instance_id] = IFlowCallResult(
                    success=False,
                    output="",
                    error=str(call_result)
                )
            else:
                result.individual_results[instance_id] = call_result
        
        # 聚合评估结果
        result.aggregated_result, result.confidence = self._aggregate_evaluation_results(
            result.individual_results,
            instances
        )
        
        # 提取建议
        result.recommendations = self._extract_recommendations(result.individual_results)
        
        result.duration = time.time() - start_time
        
        return result
    
    async def call_reflection(
        self,
        prompt: str,
        execution_result: str,
        instances: List[IForkInstance],
        context: Optional[Dict[str, Any]] = None
    ) -> MultiIFlowCallResult:
        """反思改进（自我优化）
        
        Args:
            prompt: 原始提示词
            execution_result: 执行结果
            instances: iFlow 实例列表
            context: 上下文信息
        
        Returns:
            多 iFlow 调用结果
        """
        import time
        start_time = time.time()
        
        result = MultiIFlowCallResult(strategy=MultiIFlowStrategy.REFLECTION)
        
        # 构建反思提示词
        reflection_prompt = f"""请反思以下执行过程：

原始提示：
{prompt}

执行结果：
{execution_result}

请从你的角度（{context.get('role', '反思者')}，{context.get('perspective', '多角度')}）进行反思：
1. 执行过程是否正确？
2. 结果是否满意？
3. 有哪些可以改进的地方？
4. 如何避免类似问题？
5. 对下次执行的建议
"""
        
        # 并行调用
        tasks = []
        for instance in instances:
            role_context = {
                "role": instance.role,
                "perspective": instance.perspective,
                **(context or {})
            }
            task = self._call_instance(instance, reflection_prompt, role_context)
            tasks.append((instance.id, task))
        
        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )
        
        # 收集结果
        for (instance_id, _), call_result in zip(tasks, results):
            if isinstance(call_result, Exception):
                result.individual_results[instance_id] = IFlowCallResult(
                    success=False,
                    output="",
                    error=str(call_result)
                )
            else:
                result.individual_results[instance_id] = call_result
        
        # 聚合反思结果
        result.aggregated_result, result.recommendations = self._aggregate_reflection_results(
            result.individual_results,
            instances
        )
        
        result.duration = time.time() - start_time
        
        return result
    
    async def _call_instance(
        self,
        instance: IForkInstance,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> IFlowCallResult:
        """调用单个 iFlow 实例"""
        # 获取或创建管理器
        if instance.id not in self.managers:
            self.managers[instance.id] = IFlowManager(
                iflow_command=self.iflow_command,
                default_timeout=instance.timeout,
                max_retries=self.max_retries
            )
        
        manager = self.managers[instance.id]
        
        # 调用
        return await manager.call(
            prompt=prompt,
            mode=instance.mode,
            timeout=instance.timeout,
            context=context
        )
    
    def _aggregate_parallel_results(
        self,
        results: Dict[str, IFlowCallResult]
    ) -> str:
        """聚合并行结果"""
        successful = [r for r in results.values() if r.success]
        
        if not successful:
            return "所有实例调用失败"
        
        # 简单拼接所有成功结果
        aggregated = "=== 并行执行结果汇总 ===\n\n"
        for instance_id, result in results.items():
            if result.success:
                aggregated += f"--- 实例 {instance_id} ---\n"
                aggregated += result.output[:500] + "\n\n"
        
        return aggregated
    
    def _analyze_consensus(
        self,
        results: Dict[str, IFlowCallResult],
        instances: List[IForkInstance]
    ) -> Tuple[float, List[str]]:
        """分析共识程度"""
        successful = [(inst.id, r) for inst in instances for r in [results.get(inst.id)] if r and r.success]
        
        if len(successful) < 2:
            return 0.0, []
        
        # 简化的共识分析：比较关键词
        # 实际应用中可以使用更复杂的 NLP 算法
        outputs = [r.output for _, r in successful]
        
        # 提取共同关键词
        all_keywords = set()
        for output in outputs:
            words = output.split()
            all_keywords.update(words[:50])  # 取前50个词
        
        common_keywords = []
        for keyword in all_keywords:
            count = sum(1 for output in outputs if keyword in output)
            if count >= len(successful) * 0.5:  # 至少50%的实例包含
                common_keywords.append(keyword)
        
        # 计算共识分数
        consensus_score = len(common_keywords) / max(len(all_keywords), 1)
        
        # 识别冲突（简化版本）
        conflicts = []
        if consensus_score < 0.5:
            conflicts.append("各实例观点差异较大")
        
        return min(consensus_score, 1.0), conflicts
    
    def _aggregate_consensus_results(
        self,
        results: Dict[str, IFlowCallResult],
        instances: List[IForkInstance],
        consensus_score: float
    ) -> str:
        """聚合共识结果"""
        aggregated = f"=== 共识决策结果（共识度: {consensus_score:.1%}）===\n\n"
        
        for instance in instances:
            result = results.get(instance.id)
            if result and result.success:
                aggregated += f"--- {instance.role} ({instance.perspective}) ---\n"
                aggregated += result.output[:300] + "\n\n"
        
        aggregated += "=== 共识建议 ===\n"
        if consensus_score > 0.7:
            aggregated += "各实例观点较为一致，可以采纳综合建议\n"
        elif consensus_score > 0.4:
            aggregated += "各实例观点有差异，建议进一步讨论\n"
        else:
            aggregated += "各实例观点差异较大，建议重新评估\n"
        
        return aggregated
    
    def _aggregate_evaluation_results(
        self,
        results: Dict[str, IFlowCallResult],
        instances: List[IForkInstance]
    ) -> Tuple[str, float]:
        """聚合评估结果"""
        aggregated = "=== 多角度评估结果 ===\n\n"
        
        scores = []
        for instance in instances:
            result = results.get(instance.id)
            if result and result.success:
                aggregated += f"--- {instance.role} 评估 ---\n"
                aggregated += result.output[:400] + "\n\n"
                
                # 尝试提取评分
                import re
                score_match = re.search(r'评分[：:]\s*(\d+(?:\.\d+)?)', result.output)
                if score_match:
                    scores.append(float(score_match.group(1)))
        
        # 计算置信度
        confidence = 0.0
        if scores:
            avg_score = sum(scores) / len(scores)
            confidence = avg_score / 10.0  # 转换为 0-1 范围
            
            aggregated += f"=== 综合评分 ===\n"
            aggregated += f"平均评分: {avg_score:.1f}/10\n"
            aggregated += f"置信度: {confidence:.1%}\n"
        
        return aggregated, confidence
    
    def _extract_recommendations(
        self,
        results: Dict[str, IFlowCallResult]
    ) -> List[str]:
        """提取建议"""
        recommendations = []
        
        for result in results.values():
            if result.success:
                # 简单的建议提取（实际应用中可以使用更复杂的解析）
                lines = result.output.split('\n')
                for line in lines:
                    if any(keyword in line for keyword in ['建议', 'recommend', '应该']):
                        recommendations.append(line.strip())
        
        return recommendations[:10]  # 最多返回10条建议
    
    def _aggregate_reflection_results(
        self,
        results: Dict[str, IFlowCallResult],
        instances: List[IForkInstance]
    ) -> Tuple[str, List[str]]:
        """聚合反思结果"""
        aggregated = "=== 反思改进结果 ===\n\n"
        
        all_recommendations = []
        
        for instance in instances:
            result = results.get(instance.id)
            if result and result.success:
                aggregated += f"--- {instance.role} 反思 ---\n"
                aggregated += result.output[:400] + "\n\n"
                
                # 提取建议
                import re
                pattern = r'(?:改进|避免|建议)\s*[:：]\s*(.+)'
                matches = re.findall(pattern, result.output)
                all_recommendations.extend(matches)
        
        aggregated += "=== 综合改进建议 ===\n"
        for i, rec in enumerate(all_recommendations[:5], 1):
            aggregated += f"{i}. {rec}\n"
        
        return aggregated, all_recommendations[:10]
    
    def get_predefined_roles(self) -> Dict[str, IForkInstance]:
        """获取预定义角色"""
        return self.predefined_roles.copy()
    
    def get_instances_by_perspective(
        self,
        perspective: str
    ) -> List[IForkInstance]:
        """根据视角获取实例"""
        return [
            inst for inst in self.predefined_roles.values()
            if perspective.lower() in inst.perspective.lower()
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_calls = 0
        total_success = 0
        total_duration = 0.0
        
        for manager in self.managers.values():
            stats = manager.get_statistics()
            total_calls += stats["call_count"]
            total_success += stats["success_count"]
            total_duration += stats["total_duration"]
        
        success_rate = total_success / total_calls if total_calls > 0 else 0.0
        avg_duration = total_duration / total_success if total_success > 0 else 0.0
        
        return {
            "managers_count": len(self.managers),
            "total_calls": total_calls,
            "total_success": total_success,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "average_duration": avg_duration
        }


# 全局多 iflow 管理器实例
_global_multi_iflow_manager = None


def get_multi_iflow_manager(
    iflow_command: str = "iflow",
    default_timeout: int = 300,
    max_retries: int = 3
) -> MultiIFlowManager:
    """获取全局多 iflow 管理器实例"""
    global _global_multi_iflow_manager
    
    if _global_multi_iflow_manager is None:
        _global_multi_iflow_manager = MultiIFlowManager(
            iflow_command=iflow_command,
            default_timeout=default_timeout,
            max_retries=max_retries
        )
    
    return _global_multi_iflow_manager


def reset_multi_iflow_manager():
    """重置全局多 iflow 管理器"""
    global _global_multi_iflow_manager
    _global_multi_iflow_manager = None
