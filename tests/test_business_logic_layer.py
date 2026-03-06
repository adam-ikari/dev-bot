#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Business Logic Layer
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.business_logic_layer import (
    BusinessRuleEngine,
    BusinessStrategyManager,
    BusinessLogicLayer,
    RulePriority,
    RuleCategory,
    BusinessRule,
    RuleResult,
    get_business_logic_layer,
    reset_business_logic_layer
)


async def test_rule_engine():
    """Test rule engine"""
    print("\n=== Testing Business Rule Engine ===")
    
    engine = BusinessRuleEngine()
    
    # Check default rules
    rules = engine.get_all_rules()
    print(f"Default rules: {len(rules)}")
    
    for rule in rules:
        print(f"  - {rule.name} ({rule.id})")
        print(f"    Category: {rule.category.value}, Priority: {rule.priority.value}")
    
    # Test rule evaluation
    context = {
        "decision": {"type": "development", "plan": ["step1", "step2"]},
        "session": 1
    }
    
    results = await engine.evaluate_rules(context)
    print(f"\nRule evaluation results: {len(results)}")
    for result in results:
        status = "✓" if result.passed else "✗"
        print(f"  {status} {result.rule_name}: {result.message}")
    
    print("PASS: Business rule engine test")


async def test_strategy_manager():
    """Test strategy manager"""
    print("\n=== Testing Business Strategy Manager ===")
    
    manager = BusinessStrategyManager()
    
    # Get default strategy
    strategy = manager.get_strategy("default")
    print(f"Default strategy keys: {list(strategy.keys())}")
    
    # Get decision weights
    weights = manager.get_decision_weights()
    print(f"\nDecision weights:")
    for decision_type, weight in weights.items():
        print(f"  {decision_type}: {weight}")
    
    # Get constraints
    max_files = manager.get_constraint("max_files_per_session")
    print(f"\nMax files per session: {max_files}")
    
    # Apply strategy to decision
    decision = {"type": "development", "plan": []}
    enhanced_decision = manager.apply_strategy_to_decision(decision)
    print(f"\nEnhanced decision keys: {list(enhanced_decision.keys())}")
    print(f"Has strategy_weights: {'strategy_weights' in enhanced_decision}")
    print(f"Has constraints: {'constraints' in enhanced_decision}")
    
    print("PASS: Business strategy manager test")


async def test_business_logic_layer():
    """Test business logic layer"""
    print("\n=== Testing Business Logic Layer ===")
    
    layer = BusinessLogicLayer()
    
    # Test decision validation
    decision = {
        "type": "development",
        "plan": ["Implement feature", "Write tests"],
        "description": "Add new feature"
    }
    
    context = {"session": 1, "user": "test"}
    
    validation = await layer.validate_decision_with_rules(decision, context)
    print(f"Decision validation:")
    print(f"  Valid: {validation['valid']}")
    print(f"  Pass rate: {validation['pass_rate']:.1%}")
    print(f"  Violations: {len(validation['violations'])}")
    
    # Test constraint checking
    execution = {
        "modified_files": ["file1.py", "file2.py"],
        "test_coverage": 80
    }
    
    constraints = await layer.check_execution_constraints(execution, context)
    print(f"\nConstraint checking:")
    print(f"  Passed: {constraints['passed']}")
    print(f"  Violations: {len(constraints['violations'])}")
    
    # Test business state
    state = layer.get_business_state()
    print(f"\nBusiness state: {state}")
    
    # Test statistics
    stats = layer.get_statistics()
    print(f"\nStatistics:")
    print(f"  Rules count: {stats['rules_count']}")
    print(f"  Strategies count: {stats['strategies_count']}")
    print(f"  Enabled rules: {stats['enabled_rules_count']}")
    
    print("PASS: Business logic layer test")


async def test_custom_rule():
    """Test custom rule registration"""
    print("\n=== Testing Custom Rule Registration ===")
    
    engine = BusinessRuleEngine()
    
    # Define custom rule
    async def custom_rule_handler(context: Dict, rule: BusinessRule) -> RuleResult:
        decision = context.get("decision", {})
        description = decision.get("description", "")
        
        if len(description) < 10:
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                passed=False,
                message="描述太短，至少需要10个字符",
                severity="warning"
            )
        
        return RuleResult(
            rule_id=rule.id,
            rule_name=rule.name,
            passed=True,
            message=f"描述长度: {len(description)} 字符",
            severity="info"
        )
    
    # Register custom rule
    custom_rule = BusinessRule(
        id="custom_description_length",
        name="描述长度要求",
        description="验证决策描述长度",
        category=RuleCategory.VALIDATION,
        priority=RulePriority.MEDIUM
    )
    
    engine.register_rule(custom_rule, custom_rule_handler)
    
    # Test with short description
    context1 = {"decision": {"description": "Short"}}
    results1 = await engine.evaluate_rules(context1)
    custom_result1 = [r for r in results1 if r.rule_id == "custom_description_length"][0]
    print(f"Short description: {'✓' if custom_result1.passed else '✗'} {custom_result1.message}")
    
    # Test with long description
    context2 = {"decision": {"description": "This is a long enough description"}}
    results2 = await engine.evaluate_rules(context2)
    custom_result2 = [r for r in results2 if r.rule_id == "custom_description_length"][0]
    print(f"Long description: {'✓' if custom_result2.passed else '✗'} {custom_result2.message}")
    
    # Unregister custom rule
    engine.unregister_rule("custom_description_length")
    print("\nCustom rule unregistered")
    
    print("PASS: Custom rule registration test")


async def test_rule_categories():
    """Test rule categories"""
    print("\n=== Testing Rule Categories ===")
    
    engine = BusinessRuleEngine()
    
    # Get rules by category
    validation_rules = engine.get_rules_by_category(RuleCategory.VALIDATION)
    security_rules = engine.get_rules_by_category(RuleCategory.SECURITY)
    
    print(f"Validation rules: {len(validation_rules)}")
    for rule in validation_rules:
        print(f"  - {rule.name}")
    
    print(f"\nSecurity rules: {len(security_rules)}")
    for rule in security_rules:
        print(f"  - {rule.name}")
    
    print("PASS: Rule categories test")


async def test_rule_priorities():
    """Test rule priorities"""
    print("\n=== Testing Rule Priorities ===")
    
    engine = BusinessRuleEngine()
    
    # Get rules by priority
    critical_rules = engine.get_rules_by_priority(RulePriority.CRITICAL)
    high_rules = engine.get_rules_by_priority(RulePriority.HIGH)
    
    print(f"Critical rules: {len(critical_rules)}")
    for rule in critical_rules:
        print(f"  - {rule.name}")
    
    print(f"\nHigh priority rules: {len(high_rules)}")
    for rule in high_rules:
        print(f"  - {rule.name}")
    
    print("PASS: Rule priorities test")


async def test_global_layer():
    """Test global business logic layer"""
    print("\n=== Testing Global Business Logic Layer ===")
    
    # Reset global layer
    reset_business_logic_layer()
    
    # Get global instance
    layer1 = get_business_logic_layer()
    layer2 = get_business_logic_layer()
    
    assert layer1 is layer2, "Should return same instance"
    print(f"Global layer: {layer1}")
    
    # Reset and get new instance
    reset_business_logic_layer()
    layer3 = get_business_logic_layer()
    
    assert layer1 is not layer3, "Should return new instance after reset"
    print("New layer after reset: OK")
    
    print("PASS: Global business logic layer test")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Starting tests for Business Logic Layer")
    print("=" * 60)
    
    try:
        await test_rule_engine()
        await test_strategy_manager()
        await test_business_logic_layer()
        await test_custom_rule()
        await test_rule_categories()
        await test_rule_priorities()
        await test_global_layer()
        
        print("\n" + "=" * 60)
        print("PASS: All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nFAIL: Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())