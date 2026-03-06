#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 循环业务逻辑层

在 AI 循环中体现业务逻辑，包括：
1. 业务规则引擎：定义和执行业务规则
2. 策略管理器：管理业务策略
3. 验证器：验证决策和执行
4. 约束管理：管理业务约束
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable


class RulePriority(Enum):
    """规则优先级"""
    CRITICAL = "critical"  # 关键规则，必须满足
    HIGH = "high"  # 高优先级
    MEDIUM = "medium"  # 中等优先级
    LOW = "low"  # 低优先级


class RuleCategory(Enum):
    """规则类别"""
    VALIDATION = "validation"  # 验证规则
    CONSTRAINT = "constraint"  # 约束规则
    POLICY = "policy"  # 策略规则
    SECURITY = "security"  # 安全规则
    PERFORMANCE = "performance"  # 性能规则
    QUALITY = "quality"  # 质量规则


@dataclass
class BusinessRule:
    """业务规则"""
    id: str
    name: str
    description: str
    category: RuleCategory
    priority: RulePriority
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "parameters": self.parameters
        }


class RuleResult:
    """规则执行结果"""
    
    def __init__(
        self,
        rule_id: str,
        rule_name: str,
        passed: bool,
        message: str = "",
        severity: str = "info",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.passed = passed
        self.message = message
        self.severity = severity
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "passed": self.passed,
            "message": self.message,
            "severity": self.severity,
            "metadata": self.metadata
        }


class BusinessRuleEngine:
    """业务规则引擎
    
    管理和执行业务规则
    """
    
    def __init__(self):
        self.rules: Dict[str, BusinessRule] = {}
        self.rule_handlers: Dict[str, Callable] = {}
        
        # 注册默认规则
        self._register_default_rules()
        
        print(f"[业务规则引擎] 初始化完成，已注册 {len(self.rules)} 条规则")
    
    def register_rule(
        self,
        rule: BusinessRule,
        handler: Callable
    ):
        """注册规则
        
        Args:
            rule: 业务规则
            handler: 规则处理函数
        """
        self.rules[rule.id] = rule
        self.rule_handlers[rule.id] = handler
        
        print(f"[业务规则引擎] 注册规则: {rule.name} ({rule.id})")
    
    def unregister_rule(self, rule_id: str):
        """注销规则"""
        if rule_id in self.rules:
            rule_name = self.rules[rule_id].name
            del self.rules[rule_id]
            del self.rule_handlers[rule_id]
            print(f"[业务规则引擎] 注销规则: {rule_name} ({rule_id})")
    
    def enable_rule(self, rule_id: str):
        """启用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
    
    def disable_rule(self, rule_id: str):
        """禁用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
    
    async def evaluate_rules(
        self,
        context: Dict[str, Any],
        category: Optional[RuleCategory] = None
    ) -> List[RuleResult]:
        """评估规则
        
        Args:
            context: 上下文信息
            category: 规则类别（可选）
        
        Returns:
            规则执行结果列表
        """
        results = []
        
        for rule_id, rule in self.rules.items():
            # 检查规则是否启用
            if not rule.enabled:
                continue
            
            # 检查类别过滤
            if category and rule.category != category:
                continue
            
            # 执行规则
            try:
                handler = self.rule_handlers[rule_id]
                result = await handler(context, rule)
                results.append(result)
            except Exception as e:
                # 规则执行失败
                results.append(RuleResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    passed=False,
                    message=f"规则执行失败: {e}",
                    severity="error"
                ))
        
        return results
    
    async def validate_decision(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[RuleResult]:
        """验证决策"""
        decision_context = {
            "type": "decision",
            "decision": decision,
            **context
        }
        
        return await self.evaluate_rules(
            decision_context,
            category=RuleCategory.VALIDATION
        )
    
    async def check_constraints(
        self,
        execution: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[RuleResult]:
        """检查约束"""
        constraint_context = {
            "type": "execution",
            "execution": execution,
            **context
        }
        
        return await self.evaluate_rules(
            constraint_context,
            category=RuleCategory.CONSTRAINT
        )
    
    def get_rules_by_category(self, category: RuleCategory) -> List[BusinessRule]:
        """获取指定类别的规则"""
        return [
            rule for rule in self.rules.values()
            if rule.category == category
        ]
    
    def get_rules_by_priority(self, priority: RulePriority) -> List[BusinessRule]:
        """获取指定优先级的规则"""
        return [
            rule for rule in self.rules.values()
            if rule.priority == priority
        ]
    
    def get_all_rules(self) -> List[BusinessRule]:
        """获取所有规则"""
        return list(self.rules.values())
    
    def _register_default_rules(self):
        """注册默认规则"""
        
        # 规则1：决策必须包含类型
        async def rule_decision_has_type(context: Dict, rule: BusinessRule) -> RuleResult:
            decision = context.get("decision", {})
            decision_type = decision.get("type")
            
            if not decision_type:
                return RuleResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    passed=False,
                    message="决策必须包含类型字段",
                    severity="error"
                )
            
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                passed=True,
                message=f"决策类型: {decision_type}",
                severity="info"
            )
        
        self.register_rule(
            BusinessRule(
                id="decision_has_type",
                name="决策必须包含类型",
                description="验证决策是否包含类型字段",
                category=RuleCategory.VALIDATION,
                priority=RulePriority.CRITICAL
            ),
            rule_decision_has_type
        )
        
        # 规则2：决策必须有计划
        async def rule_decision_has_plan(context: Dict, rule: BusinessRule) -> RuleResult:
            decision = context.get("decision", {})
            plan = decision.get("plan")
            
            if not plan:
                return RuleResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    passed=False,
                    message="决策必须包含执行计划",
                    severity="error"
                )
            
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                passed=True,
                message=f"执行计划包含 {len(plan) if isinstance(plan, list) else 1} 个步骤",
                severity="info"
            )
        
        self.register_rule(
            BusinessRule(
                id="decision_has_plan",
                name="决策必须有执行计划",
                description="验证决策是否包含执行计划",
                category=RuleCategory.VALIDATION,
                priority=RulePriority.HIGH
            ),
            rule_decision_has_plan
        )
        
        # 规则3：单次修改文件数量限制
        async def rule_max_files_modified(context: Dict, rule: BusinessRule) -> RuleResult:
            execution = context.get("execution", {})
            modified_files = execution.get("modified_files", [])
            max_files = rule.parameters.get("max_files", 10)
            
            if len(modified_files) > max_files:
                return RuleResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    passed=False,
                    message=f"单次修改文件数量超过限制 ({len(modified_files)} > {max_files})",
                    severity="warning"
                )
            
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                passed=True,
                message=f"修改文件数量: {len(modified_files)} (限制: {max_files})",
                severity="info"
            )
        
        self.register_rule(
            BusinessRule(
                id="max_files_modified",
                name="单次修改文件数量限制",
                description="限制单次修改的文件数量",
                category=RuleCategory.CONSTRAINT,
                priority=RulePriority.MEDIUM,
                parameters={"max_files": 10}
            ),
            rule_max_files_modified
        )
        
        # 规则4：测试覆盖率要求
        async def rule_test_coverage(context: Dict, rule: BusinessRule) -> RuleResult:
            execution = context.get("execution", {})
            test_coverage = execution.get("test_coverage", 0)
            min_coverage = rule.parameters.get("min_coverage", 70)
            
            if test_coverage < min_coverage:
                return RuleResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    passed=False,
                    message=f"测试覆盖率不足 ({test_coverage}% < {min_coverage}%)",
                    severity="warning"
                )
            
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                passed=True,
                message=f"测试覆盖率: {test_coverage}% (要求: {min_coverage}%)",
                severity="info"
            )
        
        self.register_rule(
            BusinessRule(
                id="test_coverage",
                name="测试覆盖率要求",
                description="要求代码测试覆盖率达到指定标准",
                category=RuleCategory.QUALITY,
                priority=RulePriority.HIGH,
                parameters={"min_coverage": 70}
            ),
            rule_test_coverage
        )
        
        # 规则5：禁止修改核心文件
        async def rule_protect_core_files(context: Dict, rule: BusinessRule) -> RuleResult:
            execution = context.get("execution", {})
            modified_files = execution.get("modified_files", [])
            protected_files = rule.parameters.get("protected_files", [])
            
            violations = []
            for file_path in modified_files:
                for protected in protected_files:
                    if protected in file_path:
                        violations.append(file_path)
            
            if violations:
                return RuleResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    passed=False,
                    message=f"尝试修改受保护文件: {', '.join(violations)}",
                    severity="error"
                )
            
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                passed=True,
                message="未修改受保护文件",
                severity="info"
            )
        
        self.register_rule(
            BusinessRule(
                id="protect_core_files",
                name="禁止修改核心文件",
                description="禁止修改核心系统文件",
                category=RuleCategory.SECURITY,
                priority=RulePriority.CRITICAL,
                parameters={
                    "protected_files": [
                        "dev_bot/core.py",
                        "dev_bot/main.py",
                        "dev_bot/ipc.py"
                    ]
                }
            ),
            rule_protect_core_files
        )


class BusinessStrategyManager:
    """业务策略管理器
    
    管理业务策略和决策偏好
    """
    
    def __init__(self):
        self.strategies: Dict[str, Dict[str, Any]] = {}
        
        # 默认策略
        self.strategies["default"] = {
            "decision_weights": {
                "development": 0.3,
                "debugging": 0.2,
                "optimization": 0.15,
                "refactoring": 0.1,
                "feature": 0.1,
                "bug_fix": 0.1,
                "documentation": 0.05,
                "testing": 0.0
            },
            "max_execution_time": 600,
            "max_files_per_session": 10,
            "require_tests": True,
            "min_test_coverage": 70,
            "auto_commit": True,
            "review_before_commit": True
        }
        
        print(f"[业务策略管理器] 初始化完成，已加载 {len(self.strategies)} 个策略")
    
    def get_strategy(self, strategy_id: str = "default") -> Dict[str, Any]:
        """获取策略"""
        return self.strategies.get(strategy_id, self.strategies["default"]).copy()
    
    def set_strategy(self, strategy_id: str, strategy: Dict[str, Any]):
        """设置策略"""
        self.strategies[strategy_id] = strategy
        print(f"[业务策略管理器] 设置策略: {strategy_id}")
    
    def update_strategy(self, strategy_id: str, updates: Dict[str, Any]):
        """更新策略"""
        if strategy_id in self.strategies:
            self.strategies[strategy_id].update(updates)
            print(f"[业务策略管理器] 更新策略: {strategy_id}")
    
    def get_decision_weights(self, strategy_id: str = "default") -> Dict[str, float]:
        """获取决策权重"""
        strategy = self.get_strategy(strategy_id)
        return strategy.get("decision_weights", {})
    
    def get_constraint(self, constraint_name: str, strategy_id: str = "default") -> Any:
        """获取约束值"""
        strategy = self.get_strategy(strategy_id)
        return strategy.get(constraint_name)
    
    def apply_strategy_to_decision(
        self,
        decision: Dict[str, Any],
        strategy_id: str = "default"
    ) -> Dict[str, Any]:
        """将策略应用到决策"""
        strategy = self.get_strategy(strategy_id)
        
        # 应用决策权重
        weights = strategy.get("decision_weights", {})
        if weights:
            decision["strategy_weights"] = weights
        
        # 应用约束
        constraints = {
            "max_execution_time": strategy.get("max_execution_time"),
            "max_files_per_session": strategy.get("max_files_per_session"),
            "require_tests": strategy.get("require_tests"),
            "min_test_coverage": strategy.get("min_test_coverage")
        }
        decision["constraints"] = constraints
        
        return decision


class BusinessLogicLayer:
    """业务逻辑层
    
    整合规则引擎和策略管理器
    """
    
    def __init__(self):
        self.rule_engine = BusinessRuleEngine()
        self.strategy_manager = BusinessStrategyManager()
        
        # 业务状态
        self.business_state = {
            "session_count": 0,
            "decision_count": 0,
            "rule_violations": 0,
            "strategy_changes": 0
        }
        
        print(f"[业务逻辑层] 初始化完成")
    
    async def validate_decision_with_rules(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用规则验证决策"""
        results = await self.rule_engine.validate_decision(decision, context)
        
        # 统计违规
        violations = [r for r in results if not r.passed]
        self.business_state["rule_violations"] += len(violations)
        
        return {
            "valid": len(violations) == 0,
            "results": [r.to_dict() for r in results],
            "violations": [r.to_dict() for r in violations],
            "pass_rate": (len(results) - len(violations)) / len(results) if results else 1.0
        }
    
    async def check_execution_constraints(
        self,
        execution: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查执行约束"""
        results = await self.rule_engine.check_constraints(execution, context)
        
        # 统计违规
        violations = [r for r in results if not r.passed]
        
        return {
            "passed": len(violations) == 0,
            "results": [r.to_dict() for r in results],
            "violations": [r.to_dict() for r in violations]
        }
    
    def apply_business_strategy(
        self,
        decision: Dict[str, Any],
        strategy_id: str = "default"
    ) -> Dict[str, Any]:
        """应用业务策略"""
        return self.strategy_manager.apply_strategy_to_decision(decision, strategy_id)
    
    def get_business_state(self) -> Dict[str, Any]:
        """获取业务状态"""
        return self.business_state.copy()
    
    def update_business_state(self, updates: Dict[str, Any]):
        """更新业务状态"""
        self.business_state.update(updates)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "rules_count": len(self.rule_engine.get_all_rules()),
            "strategies_count": len(self.strategy_manager.strategies),
            "enabled_rules_count": sum(1 for r in self.rule_engine.get_all_rules() if r.enabled),
            "business_state": self.business_state
        }


# 全局业务逻辑层实例
_global_business_logic_layer = None


def get_business_logic_layer() -> BusinessLogicLayer:
    """获取全局业务逻辑层实例"""
    global _global_business_logic_layer
    
    if _global_business_logic_layer is None:
        _global_business_logic_layer = BusinessLogicLayer()
    
    return _global_business_logic_layer


def reset_business_logic_layer():
    """重置全局业务逻辑层"""
    global _global_business_logic_layer
    _global_business_logic_layer = None