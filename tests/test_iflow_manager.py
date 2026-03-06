#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test iFlow Manager
"""

import asyncio
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.iflow_manager import (
    IFlowManager,
    IFlowMode,
    IFlowCallResult,
    get_iflow_manager,
    reset_iflow_manager
)


async def test_iflow_manager_creation():
    """Test iFlow manager creation"""
    print("\n=== Testing iFlow Manager Creation ===")
    
    manager = IFlowManager(
        iflow_command="iflow",
        default_timeout=300,
        max_retries=3
    )
    
    print(f"iFlow command: {manager.iflow_command}")
    print(f"Default timeout: {manager.default_timeout}")
    print(f"Max retries: {manager.max_retries}")
    
    assert manager.iflow_command == "iflow"
    assert manager.default_timeout == 300
    assert manager.max_retries == 3
    
    print("PASS: iFlow manager creation test")


async def test_iflow_modes():
    """Test iFlow modes"""
    print("\n=== Testing iFlow Modes ===")
    
    modes = [
        (IFlowMode.PLAN, "--plan"),
        (IFlowMode.YOLO, "-y"),
        (IFlowMode.THINKING, "--thinking"),
        (IFlowMode.NORMAL, "")
    ]
    
    for mode, expected_value in modes:
        print(f"Mode: {mode.name} -> '{mode.value}'")
        assert mode.value == expected_value
    
    print("PASS: iFlow modes test")


async def test_iflow_call_result():
    """Test iFlow call result"""
    print("\n=== Testing iFlow Call Result ===")
    
    result = IFlowCallResult(
        success=True,
        output="Hello from iflow",
        error="",
        exit_code=0,
        duration=1.5
    )
    
    assert result.success is True
    assert result.output == "Hello from iflow"
    assert result.duration == 1.5
    
    # Test to_dict
    result_dict = result.to_dict()
    print(f"Result as dict: {result_dict}")
    assert result_dict["success"] is True
    assert result_dict["output"] == "Hello from iflow"
    
    print("PASS: iFlow call result test")


async def test_statistics():
    """Test statistics tracking"""
    print("\n=== Testing Statistics Tracking ===")
    
    manager = IFlowManager(
        iflow_command="iflow",
        default_timeout=300,
        max_retries=0  # No retries for testing
    )
    
    # Initial stats
    stats = manager.get_statistics()
    print(f"Initial stats: {stats}")
    assert stats["call_count"] == 0
    assert stats["success_count"] == 0
    assert stats["failure_count"] == 0
    
    # Reset stats
    manager.reset_statistics()
    stats = manager.get_statistics()
    assert stats["call_count"] == 0
    
    print("PASS: Statistics tracking test")


async def test_prompt_building():
    """Test prompt building"""
    print("\n=== Testing Prompt Building ===")
    
    manager = IFlowManager(iflow_command="iflow")
    
    # Test without context
    prompt1 = manager._build_prompt("Hello")
    assert prompt1 == "Hello"
    print("Prompt without context: OK")
    
    # Test with context
    context = {"key": "value", "number": 42}
    prompt2 = manager._build_prompt("Hello", context)
    assert "# 上下文信息" in prompt2
    assert '"key": "value"' in prompt2
    assert '"number": 42' in prompt2
    assert "Hello" in prompt2
    print("Prompt with context: OK")
    
    print("PASS: Prompt building test")


async def test_global_manager():
    """Test global manager"""
    print("\n=== Testing Global Manager ===")
    
    # Reset global manager
    reset_iflow_manager()
    
    # Get global instance
    manager1 = get_iflow_manager()
    manager2 = get_iflow_manager()
    
    assert manager1 is manager2, "Should return same instance"
    print(f"Global manager: {manager1}")
    
    # Reset and get new instance
    reset_iflow_manager()
    manager3 = get_iflow_manager()
    
    assert manager1 is not manager3, "Should return new instance after reset"
    print("New manager after reset: OK")
    
    print("PASS: Global manager test")


async def test_convenience_methods():
    """Test convenience methods"""
    print("\n=== Testing Convenience Methods ===")
    
    manager = IFlowManager(iflow_command="iflow")
    
    # Test method signatures (we won't actually call iflow in tests)
    print("call_plan method exists: ", hasattr(manager, 'call_plan'))
    print("call_yolo method exists: ", hasattr(manager, 'call_yolo'))
    print("call_thinking method exists: ", hasattr(manager, 'call_thinking'))
    
    assert hasattr(manager, 'call_plan')
    assert hasattr(manager, 'call_yolo')
    assert hasattr(manager, 'call_thinking')
    
    print("PASS: Convenience methods test")


async def test_statistics_calculation():
    """Test statistics calculation"""
    print("\n=== Testing Statistics Calculation ===")
    
    manager = IFlowManager(iflow_command="iflow")
    
    # Simulate some calls
    manager.call_count = 10
    manager.success_count = 8
    manager.failure_count = 2
    manager.total_duration = 50.0
    
    stats = manager.get_statistics()
    print(f"Statistics: {stats}")
    
    assert stats["call_count"] == 10
    assert stats["success_count"] == 8
    assert stats["failure_count"] == 2
    assert abs(stats["success_rate"] - 0.8) < 0.01
    assert abs(stats["average_duration"] - 6.25) < 0.01
    
    print("PASS: Statistics calculation test")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Starting tests for iFlow Manager")
    print("=" * 60)
    
    try:
        await test_iflow_manager_creation()
        await test_iflow_modes()
        await test_iflow_call_result()
        await test_statistics()
        await test_prompt_building()
        await test_global_manager()
        await test_convenience_methods()
        await test_statistics_calculation()
        
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