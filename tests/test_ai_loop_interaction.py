#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test AI loop interaction system
"""

import asyncio
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.ai_loop_control import AILoopController, AILoopState, AILoopCommand
from dev_bot.user_interaction import UserInteractionLayer, UserCommand


async def test_ai_loop_controller():
    """Test AI loop controller"""
    print("\n=== Testing AI Loop Controller ===")
    
    project_root = Path.cwd()
    controller = AILoopController(project_root)
    
    # Test initial state
    status = await controller.get_status()
    print(f"Initial state: {status['state']}")
    assert status['state'] == AILoopState.STOPPED.value
    
    # Test start
    print("Starting AI loop...")
    success = await controller.start()
    print(f"Start result: {success}")
    
    if success:
        # Wait a bit
        await asyncio.sleep(2)
        
        # Check status
        status = await controller.get_status()
        print(f"State after start: {status['state']}")
        
        # Test stop
        print("Stopping AI loop...")
        success = await controller.stop()
        print(f"Stop result: {success}")
        
        # Check status
        status = await controller.get_status()
        print(f"State after stop: {status['state']}")
    
    print("PASS: AI loop controller test")


async def test_user_interaction_layer():
    """Test user interaction layer"""
    print("\n=== Testing User Interaction Layer ===")
    
    project_root = Path.cwd()
    user_layer = UserInteractionLayer(project_root)
    
    # Start user layer
    await user_layer.start()
    await asyncio.sleep(1)
    
    # Test help command
    result = await user_layer.execute_command("help")
    print("Help command output:")
    print(result[:200] + "...")
    assert "可用命令" in result
    
    # Test status command
    result = await user_layer.execute_command("status")
    print("Status command output:")
    print(result)
    
    # Test unknown command
    result = await user_layer.execute_command("unknown_command")
    print(f"Unknown command result: {result}")
    assert "错误" in result
    
    # Stop user layer
    await user_layer.stop()
    
    print("PASS: User interaction layer test")


async def test_command_parsing():
    """Test command parsing"""
    print("\n=== Testing Command Parsing ===")
    
    project_root = Path.cwd()
    user_layer = UserInteractionLayer(project_root)
    
    await user_layer.start()
    await asyncio.sleep(0.5)
    
    # Test commands with arguments
    commands = [
        ("logs", "logs command"),
        ("logs 10", "logs with argument"),
        ("send test message", "send command"),
    ]
    
    for cmd, description in commands:
        result = await user_layer.execute_command(cmd)
        print(f"{description}: {result[:100]}")
    
    # Test empty command
    result = await user_layer.execute_command("")
    print(f"Empty command: {result}")
    assert "错误" in result
    
    await user_layer.stop()
    
    print("PASS: Command parsing test")


async def test_state_transitions():
    """Test state transitions"""
    print("\n=== Testing State Transitions ===")
    
    project_root = Path.cwd()
    controller = AILoopController(project_root)
    
    # Test stopped state
    status = await controller.get_status()
    print(f"Initial state: {status['state']}")
    assert status['state'] == AILoopState.STOPPED.value
    
    # Start
    success = await controller.start()
    if success:
        await asyncio.sleep(1)
        status = await controller.get_status()
        print(f"After start: {status['state']}")
        # Note: State might be RUNNING or STARTING depending on timing
        
        # Stop
        await controller.stop()
        await asyncio.sleep(0.5)
        status = await controller.get_status()
        print(f"After stop: {status['state']}")
        assert status['state'] == AILoopState.STOPPED.value
    
    print("PASS: State transitions test")


async def test_command_history():
    """Test command history"""
    print("\n=== Testing Command History ===")
    
    project_root = Path.cwd()
    user_layer = UserInteractionLayer(project_root)
    
    await user_layer.start()
    
    # Execute some commands
    commands = ["status", "ai_status", "guardian_status"]
    for cmd in commands:
        await user_layer.execute_command(cmd)
    
    # Check history
    history = user_layer.get_command_history()
    print(f"Command history: {history}")
    assert len(history) == len(commands)
    assert history == commands
    
    # Clear history
    user_layer.clear_history()
    history = user_layer.get_command_history()
    print(f"After clear: {history}")
    assert len(history) == 0
    
    await user_layer.stop()
    
    print("PASS: Command history test")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Starting tests for AI loop interaction system")
    print("=" * 60)
    
    try:
        await test_ai_loop_controller()
        await test_user_interaction_layer()
        await test_command_parsing()
        await test_state_transitions()
        await test_command_history()
        
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