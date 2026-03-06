#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Multi iFlow Manager
"""

import asyncio
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.multi_iflow_manager import (
    MultiIFlowManager,
    MultiIFlowStrategy,
    IForkInstance,
    MultiIFlowCallResult,
    get_multi_iflow_manager,
    reset_multi_iflow_manager
)


async def test_manager_creation():
    """Test manager creation"""
    print("\n=== Testing Multi iFlow Manager Creation ===")
    
    manager = MultiIFlowManager(
        iflow_command="iflow",
        default_timeout=300,
        max_retries=3
    )
    
    print(f"iFlow command: {manager.iflow_command}")
    print(f"Default timeout: {manager.default_timeout}")
    print(f"Max retries: {manager.max_retries}")
    print(f"Predefined roles: {len(manager.predefined_roles)}")
    
    assert manager.iflow_command == "iflow"
    assert len(manager.predefined_roles) == 6
    
    print("PASS: Multi iFlow manager creation test")


async def test_strategies():
    """Test multi iflow strategies"""
    print("\n=== Testing Multi iFlow Strategies ===")
    
    strategies = [
        MultiIFlowStrategy.PARALLEL,
        MultiIFlowStrategy.CONSENSUS,
        MultiIFlowStrategy.EVALUATION,
        MultiIFlowStrategy.REFLECTION,
        MultiIFlowStrategy.DEBATE
    ]
    
    for strategy in strategies:
        print(f"Strategy: {strategy.name} -> '{strategy.value}'")
    
    print("PASS: Multi iFlow strategies test")


async def test_predefined_roles():
    """Test predefined roles"""
    print("\n=== Testing Predefined Roles ===")
    
    manager = MultiIFlowManager()
    roles = manager.get_predefined_roles()
    
    print(f"Available roles: {list(roles.keys())}")
    
    for role_id, role in roles.items():
        print(f"  {role_id}: {role.role} ({role.perspective})")
        assert role.id == role_id
        assert role.role
        assert role.perspective
    
    print("PASS: Predefined roles test")


async def test_instance_creation():
    """Test instance creation"""
    print("\n=== Testing Instance Creation ===")
    
    instance = IForkInstance(
        id="custom",
        role="Custom Role",
        perspective="Custom Perspective",
        priority=5,
        timeout=600,
        mode=None  # Will use default
    )
    
    print(f"Instance ID: {instance.id}")
    print(f"Role: {instance.role}")
    print(f"Perspective: {instance.perspective}")
    print(f"Priority: {instance.priority}")
    print(f"Timeout: {instance.timeout}")
    
    assert instance.id == "custom"
    assert instance.role == "Custom Role"
    
    print("PASS: Instance creation test")


async def test_result_structure():
    """Test result structure"""
    print("\n=== Testing Result Structure ===")
    
    result = MultiIFlowCallResult(
        strategy=MultiIFlowStrategy.CONSENSUS,
        aggregated_result="Test result",
        consensus_score=0.8,
        confidence=0.9,
        conflicts=["Minor conflict"],
        recommendations=["Suggestion 1"]
    )
    
    print(f"Strategy: {result.strategy.value}")
    print(f"Consensus score: {result.consensus_score}")
    print(f"Confidence: {result.confidence}")
    
    # Test to_dict
    result_dict = result.to_dict()
    print(f"Result as dict keys: {list(result_dict.keys())}")
    
    assert result_dict["strategy"] == "consensus"
    assert result_dict["consensus_score"] == 0.8
    
    print("PASS: Result structure test")


async def test_get_instances_by_perspective():
    """Test getting instances by perspective"""
    print("\n=== Testing Get Instances by Perspective ===")
    
    manager = MultiIFlowManager()
    
    # Search for "代码" (code)
    code_instances = manager.get_instances_by_perspective("代码")
    print(f"Instances matching '代码': {[inst.id for inst in code_instances]}")
    
    # Search for "安全" (security)
    security_instances = manager.get_instances_by_perspective("安全")
    print(f"Instances matching '安全': {[inst.id for inst in security_instances]}")
    
    assert "developer" in [inst.id for inst in code_instances]
    assert "security" in [inst.id for inst in security_instances]
    
    print("PASS: Get instances by perspective test")


async def test_statistics():
    """Test statistics"""
    print("\n=== Testing Statistics ===")
    
    manager = MultiIFlowManager()
    
    stats = manager.get_statistics()
    print(f"Statistics: {stats}")
    
    assert "managers_count" in stats
    assert "total_calls" in stats
    assert "success_rate" in stats
    
    print("PASS: Statistics test")


async def test_global_manager():
    """Test global manager"""
    print("\n=== Testing Global Manager ===")
    
    # Reset global manager
    reset_multi_iflow_manager()
    
    # Get global instance
    manager1 = get_multi_iflow_manager()
    manager2 = get_multi_iflow_manager()
    
    assert manager1 is manager2, "Should return same instance"
    print(f"Global manager: {manager1}")
    
    # Reset and get new instance
    reset_multi_iflow_manager()
    manager3 = get_multi_iflow_manager()
    
    assert manager1 is not manager3, "Should return new instance after reset"
    print("New manager after reset: OK")
    
    print("PASS: Global manager test")


async def test_parallel_strategy_structure():
    """Test parallel strategy structure"""
    print("\n=== Testing Parallel Strategy Structure ===")
    
    manager = MultiIFlowManager()
    
    # Create test instances
    instances = [
        manager.predefined_roles["developer"],
        manager.predefined_roles["tester"]
    ]
    
    # Test method exists
    assert hasattr(manager, 'call_parallel')
    assert hasattr(manager, 'call_consensus')
    assert hasattr(manager, 'call_evaluation')
    assert hasattr(manager, 'call_reflection')
    
    print("All strategy methods exist: OK")
    print("PASS: Parallel strategy structure test")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Starting tests for Multi iFlow Manager")
    print("=" * 60)
    
    try:
        await test_manager_creation()
        await test_strategies()
        await test_predefined_roles()
        await test_instance_creation()
        await test_result_structure()
        await test_get_instances_by_perspective()
        await test_statistics()
        await test_global_manager()
        await test_parallel_strategy_structure()
        
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
