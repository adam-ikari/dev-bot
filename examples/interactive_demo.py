#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive demo for AI loop control

This script demonstrates the user interaction layer with AI guardian and AI loop control.
"""

import asyncio
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.user_interaction import UserInteractionLayer


async def demo():
    """Demo script"""
    print("=" * 70)
    print("Dev-Bot AI Loop Control - Interactive Demo")
    print("=" * 70)
    print()
    print("This demo shows the interaction between:")
    print("  - User (you)")
    print("  - User Interaction Layer")
    print("  - AI Guardian (monitors and recovers processes)")
    print("  - AI Loop (performs AI-driven development)")
    print()
    print("Architecture:")
    print("  User → User Interaction Layer → AI Guardian → AI Loop")
    print()
    print("=" * 70)
    print()
    
    # Create user interaction layer
    project_root = Path.cwd()
    user_layer = UserInteractionLayer(project_root)
    
    # Start the system
    print("Starting system...")
    await user_layer.start()
    await asyncio.sleep(1)
    
    print("\n" + "=" * 70)
    print("Demo Commands:")
    print("=" * 70)
    print()
    
    # Demo 1: Check initial status
    print("1. Checking initial status...")
    result = await user_layer.execute_command("status")
    print(result)
    print()
    
    # Demo 2: Check AI loop status
    print("2. Checking AI loop status...")
    result = await user_layer.execute_command("ai_status")
    print(result)
    print()
    
    # Demo 3: Check guardian status
    print("3. Checking guardian status...")
    result = await user_layer.execute_command("guardian_status")
    print(result)
    print()
    
    # Demo 4: Start AI loop
    print("4. Starting AI loop...")
    result = await user_layer.execute_command("start_ai")
    print(result)
    print()
    
    # Wait for AI loop to start
    await asyncio.sleep(3)
    
    # Demo 5: Check status after start
    print("5. Checking status after start...")
    result = await user_layer.execute_command("status")
    print(result)
    print()
    
    # Demo 6: Send a message to AI loop
    print("6. Sending a message to AI loop...")
    result = await user_layer.execute_command("send Hello from user!")
    print(result)
    print()
    
    # Demo 7: Get recent logs
    print("7. Getting recent logs...")
    result = await user_layer.execute_command("logs 10")
    print(result)
    print()
    
    # Demo 8: Pause AI loop
    print("8. Pausing AI loop...")
    result = await user_layer.execute_command("pause_ai")
    print(result)
    print()
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Demo 9: Resume AI loop
    print("9. Resuming AI loop...")
    result = await user_layer.execute_command("resume_ai")
    print(result)
    print()
    
    # Wait a bit more
    await asyncio.sleep(3)
    
    # Demo 10: Stop AI loop
    print("10. Stopping AI loop...")
    result = await user_layer.execute_command("stop_ai")
    print(result)
    print()
    
    # Wait for stop
    await asyncio.sleep(2)
    
    # Demo 11: Check final status
    print("11. Checking final status...")
    result = await user_layer.execute_command("status")
    print(result)
    print()
    
    # Demo 12: Show command history
    print("12. Command history:")
    history = user_layer.get_command_history()
    for i, cmd in enumerate(history, 1):
        print(f"  {i}. {cmd}")
    print()
    
    # Stop the system
    print("Stopping system...")
    await user_layer.stop()
    
    print()
    print("=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)
    print()
    print("To use the system interactively, run:")
    print("  python3 -m dev_bot.user_interaction")
    print()
    print("Available commands:")
    result = await user_layer.execute_command("help")
    print(result)


if __name__ == '__main__':
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
