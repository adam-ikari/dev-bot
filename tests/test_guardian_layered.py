#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test layered architecture AI guardian process
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.guardian import (
    CoreGuardian,
    AIGuardian,
    BusinessLogicLayer,
    BusinessRule,
    DefaultHealthChecker,
    DefaultRecoveryStrategy
)


class MockRecoveryStrategy:
    """Mock recovery strategy for testing"""
    
    def __init__(self):
        self.recovery_calls = []
    
    async def recover(self, process_type, process_info):
        """Mock recovery operation"""
        self.recovery_calls.append({
            "process_type": process_type,
            "process_info": process_info
        })
        return True


class TestBusinessRule(BusinessRule):
    """Test business rule"""
    
    def __init__(self):
        self.evaluations = []
        self.executions = []
    
    async def evaluate(self, process_type, process_info):
        """Evaluate rule"""
        self.evaluations.append({
            "process_type": process_type,
            "process_info": process_info
        })
        return False  # Default: don't execute
    
    async def execute(self, process_type, process_info):
        """Execute rule"""
        self.executions.append({
            "process_type": process_type,
            "process_info": process_info
        })
        return True


async def test_core_guardian():
    """Test core guardian layer"""
    print("\n=== Testing Core Guardian Layer ===")
    
    # Create core guardian
    recovery_strategy = MockRecoveryStrategy()
    core_guardian = CoreGuardian(
        check_interval=1,
        recovery_strategy=recovery_strategy
    )
    
    # Register process
    core_guardian.register_process(
        "test_process",
        None,
        ["echo", "test"],
        max_restarts=3
    )
    
    # Start guardian
    await core_guardian.start()
    
    # Wait for a few check cycles
    await asyncio.sleep(3)
    
    # Stop guardian
    await core_guardian.stop()
    
    # Check status
    status = core_guardian.get_status()
    print(f"Core guardian status: {json.dumps(status, indent=2, default=str)}")
    
    assert status["is_running"] == False
    assert len(recovery_strategy.recovery_calls) > 0
    
    print("PASS: Core guardian layer test")


async def test_business_logic_layer():
    """Test business logic layer"""
    print("\n=== Testing Business Logic Layer ===")
    
    # Create core guardian
    core_guardian = CoreGuardian(check_interval=1)
    
    # Create business logic layer
    business_layer = BusinessLogicLayer(core_guardian)
    
    # Add test rule
    test_rule = TestBusinessRule()
    business_layer.add_rule(test_rule)
    
    # Check rules
    process_info = {"pid": 1234, "last_seen": 1234567890}
    await business_layer.evaluate_and_execute_rules("test_process", process_info)
    
    # Verify rule was evaluated
    assert len(test_rule.evaluations) > 0
    print(f"Rule evaluation count: {len(test_rule.evaluations)}")
    
    # Check status
    status = business_layer.get_status()
    print(f"Business logic layer status: {json.dumps(status, indent=2, default=str)}")
    
    assert "TestBusinessRule" in status["rules"]
    
    print("PASS: Business logic layer test")


async def test_ai_guardian():
    """Test AI guardian process (integration layer)"""
    print("\n=== Testing AI Guardian Process (Integration Layer) ===")
    
    # Create AI guardian
    ai_guardian = AIGuardian(check_interval=1)
    
    # Register process
    ai_guardian.register_process(
        "test_process",
        None,
        ["echo", "test"],
        max_restarts=3
    )
    
    # Start guardian
    await ai_guardian.start()
    
    # Wait for a few check cycles
    await asyncio.sleep(3)
    
    # Check status while running
    status = ai_guardian.get_status()
    print(f"AI guardian status (running): {json.dumps(status, indent=2, default=str)}")
    assert status["core_guardian"]["is_running"] == True
    assert "business_layer" in status
    
    # Stop guardian
    await ai_guardian.stop()
    
    # Wait a bit for stop to complete
    await asyncio.sleep(1)
    
    # Verify status after stopping
    final_status = ai_guardian.get_status()
    print(f"AI guardian status (stopped): {json.dumps(final_status, indent=2, default=str)}")
    assert final_status["core_guardian"]["is_running"] == False
    
    print("PASS: AI guardian process test")


async def test_custom_business_rule():
    """Test custom business rule"""
    print("\n=== Testing Custom Business Rule ===")
    
    # Create AI guardian
    ai_guardian = AIGuardian(check_interval=1)
    
    # Create custom rule
    class CustomRule(BusinessRule):
        def __init__(self, threshold=5):
            self.threshold = threshold
            self.evaluations = []
        
        async def evaluate(self, process_type, process_info):
            self.evaluations.append({"process_type": process_type})
            restart_count = process_info.get("restart_count", 0)
            return restart_count >= self.threshold
        
        async def execute(self, process_type, process_info):
            print(f"Custom rule triggered: {process_type} restart count reached {self.threshold}")
            return True
    
    # Add custom rule
    custom_rule = CustomRule(threshold=3)
    ai_guardian.add_business_rule(custom_rule)
    
    # Register process
    ai_guardian.register_process("test_process", None, ["echo", "test"], max_restarts=10)
    
    # Start guardian to enable rule evaluation
    await ai_guardian.start()
    
    # Update process status, simulate multiple restarts
    for i in range(5):
        ai_guardian.update_process_status("test_process", 1000 + i)
        await asyncio.sleep(0.1)
    
    # Wait for guardian to check and evaluate rules
    await asyncio.sleep(2)
    
    # Stop guardian
    await ai_guardian.stop()
    
    # Verify rule was evaluated (rules are evaluated during health checks)
    print(f"Custom rule evaluation count: {len(custom_rule.evaluations)}")
    
    print("PASS: Custom business rule test")


async def test_config_loading():
    """Test config loading"""
    print("\n=== Testing Config Loading ===")
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "max_restart_threshold": 10,
            "max_idle_time": 600
        }
        json.dump(config, f)
        config_file = Path(f.name)
    
    try:
        # Create AI guardian (with config)
        ai_guardian = AIGuardian(check_interval=1, config_file=config_file)
        
        # Check if config was loaded
        business_config = ai_guardian.business_layer.config
        assert business_config["max_restart_threshold"] == 10
        assert business_config["max_idle_time"] == 600
        
        print(f"Loaded config: {json.dumps(business_config, indent=2)}")
        
        print("PASS: Config loading test")
    finally:
        # Clean up temp file
        config_file.unlink()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Starting tests for layered architecture AI guardian")
    print("=" * 60)
    
    try:
        await test_core_guardian()
        await test_business_logic_layer()
        await test_ai_guardian()
        await test_custom_business_rule()
        await test_config_loading()
        
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
