#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Command Scheduler
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.command_scheduler import (
    Command,
    CommandType,
    CommandStatus,
    CommandPriority,
    CommandQueue,
    CommandDispatcher,
    CommandScheduler,
    get_command_scheduler,
    reset_command_scheduler
)


async def test_command_creation():
    """Test command creation"""
    print("\n=== Testing Command Creation ===")
    
    command = Command(
        id="test_command_1",
        type=CommandType.DEVELOP,
        priority=CommandPriority.HIGH,
        prompt="Test prompt",
        timeout=300
    )
    
    print(f"Command ID: {command.id}")
    print(f"Command type: {command.type.value}")
    print(f"Command priority: {command.priority.value}")
    print(f"Command prompt: {command.prompt}")
    
    # Test to_dict
    command_dict = command.to_dict()
    print(f"\nCommand as dict keys: {list(command_dict.keys())}")
    
    assert command.id == "test_command_1"
    assert command.type == CommandType.DEVELOP
    
    print("PASS: Command creation test")


async def test_command_queue():
    """Test command queue"""
    print("\n=== Testing Command Queue ===")
    
    queue = CommandQueue()
    
    # Add commands with different priorities
    commands = [
        Command("cmd1", CommandType.DEVELOP, CommandPriority.NORMAL, "Prompt 1"),
        Command("cmd2", CommandType.DEBUG, CommandPriority.URGENT, "Prompt 2"),
        Command("cmd3", CommandType.TEST, CommandPriority.HIGH, "Prompt 3"),
        Command("cmd4", CommandType.ANALYZE, CommandPriority.LOW, "Prompt 4"),
    ]
    
    for cmd in commands:
        queue.add_command(cmd)
    
    # Get queue status
    status = queue.get_queue_status()
    print(f"Queue status: {status}")
    print(f"Queue length: {status['queue_length']}")
    print(f"Pending: {status['pending']}")
    
    # Get next command
    next_cmd = queue.get_next_command()
    print(f"\nNext command: {next_cmd.id if next_cmd else None}")
    print(f"Expected: cmd2 (URGENT priority)")
    
    assert next_cmd.id == "cmd2" if next_cmd else False
    
    print("PASS: Command queue test")


async def test_command_dispatcher():
    """Test command dispatcher"""
    print("\n=== Testing Command Dispatcher ===")
    
    dispatcher = CommandDispatcher()
    
    # Create a simple command (without actually calling iflow)
    command = Command(
        id="test_dispatch",
        type=CommandType.ANALYZE,
        priority=CommandPriority.NORMAL,
        prompt="Test dispatch",
        timeout=5  # Short timeout for testing
    )
    
    print(f"Dispatcher initialized")
    print(f"iflow command: {dispatcher.iflow_command}")
    print(f"Queue status: {dispatcher.command_queue.get_queue_status()}")
    
    # Test queue status
    dispatcher.command_queue.add_command(command)
    queue_status = dispatcher.command_queue.get_queue_status()
    print(f"\nAfter adding command: {queue_status}")
    
    print("PASS: Command dispatcher test")


async def test_command_priorities():
    """Test command priorities"""
    print("\n=== Testing Command Priorities ===")
    
    queue = CommandQueue()
    
    # Add commands in random order
    commands = [
        Command("low", CommandType.TEST, CommandPriority.LOW, "Low priority"),
        Command("urgent", CommandType.DEBUG, CommandPriority.URGENT, "Urgent priority"),
        Command("high", CommandType.DEVELOP, CommandPriority.HIGH, "High priority"),
        Command("normal", CommandType.ANALYZE, CommandPriority.NORMAL, "Normal priority"),
    ]
    
    for cmd in commands:
        queue.add_command(cmd)
    
    # Check order
    queued = queue.get_pending_commands()
    print(f"Queued commands order:")
    for i, cmd in enumerate(queued):
        print(f"  {i+1}. {cmd.id} ({cmd.priority.value})")
    
    # Urgent should be first
    assert queued[0].priority == CommandPriority.URGENT
    
    print("PASS: Command priorities test")


async def test_command_dependencies():
    """Test command dependencies"""
    print("\n=== Testing Command Dependencies ===")
    
    queue = CommandQueue()
    
    # Create commands with dependencies
    cmd1 = Command("cmd1", CommandType.DEVELOP, CommandPriority.HIGH, "Step 1")
    cmd2 = Command("cmd2", CommandType.TEST, CommandPriority.HIGH, "Step 2", dependencies=["cmd1"])
    cmd3 = Command("cmd3", CommandType.DEPLOY, CommandPriority.NORMAL, "Step 3", dependencies=["cmd2"])
    cmd4 = Command("cmd4", CommandType.ANALYZE, CommandPriority.LOW, "Independent", dependencies=[])
    
    queue.add_command(cmd4)  # Independent
    queue.add_command(cmd1)  # No dependencies
    queue.add_command(cmd3)  # Depends on cmd2
    queue.add_command(cmd2)  # Depends on cmd1
    
    # Get next commands
    print("Command order with dependencies:")
    for i in range(4):
        cmd = queue.get_next_command()
        if cmd:
            print(f"  {i+1}. {cmd.id} (deps: {cmd.dependencies})")
            queue.mark_completed(cmd.id, type('obj', (object,), {'command_id': cmd.id, 'status': 'completed'})())
        else:
            break
    
    print("PASS: Command dependencies test")


async def test_command_scheduler():
    """Test command scheduler"""
    print("\n=== Testing Command Scheduler ===")
    
    scheduler = CommandScheduler(Path.cwd())
    
    # Check generators
    print(f"Generators count: {len(scheduler.command_generators)}")
    print(f"Generator types: {list(scheduler.command_generators.keys())}")
    
    # Generate command
    context = {"session": 1, "task": "Test task"}
    command = scheduler.generate_command(CommandType.ANALYZE, context)
    
    if command:
        print(f"\nGenerated command:")
        print(f"  ID: {command.id}")
        print(f"  Type: {command.type.value}")
        print(f"  Priority: {command.priority.value}")
        print(f"  Prompt: {command.prompt[:50]}...")
        
        # Get statistics
        stats = scheduler.get_statistics()
        print(f"\nStatistics:")
        print(f"  Generators: {stats['generators_count']}")
        print(f"  Queue: {stats['queue']}")
    
    print("PASS: Command scheduler test")


async def test_custom_generator():
    """Test custom generator registration"""
    print("\n=== Testing Custom Generator Registration ===")
    
    scheduler = CommandScheduler(Path.cwd())
    
    # Define custom generator
    def custom_generator(context: Dict) -> Command:
        task = context.get("task", "Custom task")
        return Command(
            id=f"custom_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type=CommandType.CUSTOM,
            priority=CommandPriority.NORMAL,
            prompt=f"执行自定义任务: {task}",
            context=context,
            timeout=300
        )
    
    # Register custom generator
    scheduler.register_generator(CommandType.CUSTOM, custom_generator)
    
    print(f"Registered custom generator for: {CommandType.CUSTOM.value}")
    
    # Test custom generator
    context = {"session": 1, "task": "Custom task"}
    command = scheduler.generate_command(CommandType.CUSTOM, context)
    
    if command:
        print(f"Custom command generated: {command.id}")
        assert command.type == CommandType.CUSTOM
    
    print("PASS: Custom generator registration test")


async def test_global_scheduler():
    """Test global scheduler"""
    print("\n=== Testing Global Scheduler ===")
    
    # Reset global scheduler
    reset_command_scheduler()
    
    # Get global instance
    scheduler1 = get_command_scheduler(Path.cwd())
    scheduler2 = get_command_scheduler(Path.cwd())
    
    assert scheduler1 is scheduler2, "Should return same instance"
    print(f"Global scheduler: {scheduler1}")
    
    # Reset and get new instance
    reset_command_scheduler()
    scheduler3 = get_command_scheduler(Path.cwd())
    
    assert scheduler1 is not scheduler3, "Should return new instance after reset"
    print("New scheduler after reset: OK")
    
    print("PASS: Global scheduler test")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Starting tests for Command Scheduler")
    print("=" * 60)
    
    try:
        await test_command_creation()
        await test_command_queue()
        await test_command_dispatcher()
        await test_command_priorities()
        await test_command_dependencies()
        await test_command_scheduler()
        await test_custom_generator()
        await test_global_scheduler()
        
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