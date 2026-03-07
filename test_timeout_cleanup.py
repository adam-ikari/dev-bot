#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test timeout cleanup functionality

Verify that iflow processes are properly cleaned up when they timeout
"""

import asyncio
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dev_bot.iflow_manager import get_iflow_manager, IFlowMode


async def count_node_processes():
    """Count Node processes running iflow"""
    result = subprocess.run(
        ['ps', 'aux'],
        capture_output=True,
        text=True
    )
    
    count = 0
    pids = []
    for line in result.stdout.split('\n'):
        if 'node' in line and 'iflow' in line and 'grep' not in line:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    pid = int(parts[1])
                    count += 1
                    pids.append(pid)
                except ValueError:
                    continue
    return count, pids


async def test_timeout_cleanup():
    """Test timeout cleanup"""
    print("=" * 60)
    print("Test: iflow Timeout Cleanup")
    print("=" * 60)
    
    # Get initial process count
    initial_count, initial_pids = await count_node_processes()
    print(f"\nInitial Node process count: {initial_count}")
    print(f"Initial PIDs: {initial_pids}")
    
    # Create iflow manager with short timeout
    iflow_manager = get_iflow_manager(
        iflow_command="iflow",
        default_timeout=5,  # 5 second timeout
        max_retries=1
    )
    
    print("\n[Step 1] Testing timeout scenario...")
    print("-" * 60)
    
    # Try to call iflow with a long-running task that will timeout
    result = await iflow_manager.call(
        prompt="Wait for 60 seconds without doing anything",
        mode=IFlowMode.NORMAL,
        timeout=3  # 3 second timeout
    )
    
    print(f"Call result: {result.success}")
    if not result.success:
        print(f"Timeout error: {result.error}")
    
    # Wait for cleanup
    print("\n[Step 2] Waiting for process cleanup...")
    print("-" * 60)
    await asyncio.sleep(3)
    
    # Check process count after timeout
    after_count, after_pids = await count_node_processes()
    print(f"\nNode process count after timeout: {after_count}")
    print(f"PIDs after timeout: {after_pids}")
    
    # Compare counts
    print("\n[Step 3] Analysis")
    print("-" * 60)
    print(f"Initial processes: {initial_count}")
    print(f"Processes after timeout: {after_count}")
    print(f"Difference: {after_count - initial_count}")
    
    if after_count == initial_count:
        print("✓ PASS: No process leakage detected")
        print("  All timeout processes were properly cleaned up")
    else:
        leaked = after_count - initial_count
        print(f"✗ FAIL: {leaked} process(es) leaked")
        print("  Some timeout processes were not cleaned up")
    
    # Run multiple timeout tests to stress test
    print("\n[Step 4] Stress test with multiple timeouts...")
    print("-" * 60)
    
    stress_iterations = 5
    for i in range(stress_iterations):
        print(f"  Iteration {i+1}/{stress_iterations}...")
        await iflow_manager.call(
            prompt=f"Test iteration {i+1}",
            mode=IFlowMode.NORMAL,
            timeout=2
        )
        await asyncio.sleep(1)
    
    # Final check
    final_count, final_pids = await count_node_processes()
    print(f"\nFinal Node process count: {final_count}")
    print(f"Final PIDs: {final_pids}")
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    stats = iflow_manager.get_statistics()
    print(f"\nCall Statistics:")
    print(f"  Total calls: {stats['call_count']}")
    print(f"  Success: {stats['success_count']}")
    print(f"  Failures: {stats['failure_count']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    
    print(f"\nProcess Leakage Test:")
    if final_count == initial_count:
        print("  ✓ PASS: No process leakage after stress test")
    else:
        leaked = final_count - initial_count
        print(f"  ✗ FAIL: {leaked} process(es) leaked after stress test")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    try:
        asyncio.run(test_timeout_cleanup())
    except KeyboardInterrupt:
        print("\nTest interrupted")
