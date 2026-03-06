#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test process manager
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev_bot.process_manager import (
    ProcessManager,
    get_process_manager,
    reset_process_manager,
    start_ai_loop,
    stop_ai_loop
)


async def test_process_manager_creation():
    """Test process manager creation"""
    print("\n=== Testing Process Manager Creation ===")
    
    manager = ProcessManager()
    
    # Test Python interpreter
    python_interp = manager.get_python_interpreter()
    print(f"Python interpreter: {python_interp}")
    assert python_interp == sys.executable
    
    # Test initial state
    assert len(manager.processes) == 0
    assert manager.get_running_process_count() == 0
    
    print("PASS: Process manager creation test")


async def test_process_creation():
    """Test process creation"""
    print("\n=== Testing Process Creation ===")
    
    manager = ProcessManager()
    
    # Create a simple test script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("#!/usr/bin/env python3\n")
        f.write("import sys\n")
        f.write("print('Hello from subprocess')\n")
        f.write("sys.exit(0)\n")
        test_script = Path(f.name)
    
    try:
        # Create process
        process = await manager.create_process(
            process_id="test_process",
            script_path=test_script,
            args=[]
        )
        
        assert process is not None
        assert manager.is_process_running("test_process")
        
        pid = manager.get_process_pid("test_process")
        print(f"Process created with PID: {pid}")
        assert pid is not None
        
        # Wait for process to complete
        await process.wait()
        
        # Cleanup
        manager.cleanup_finished_processes()
        assert len(manager.processes) == 0
        
        print("PASS: Process creation test")
        
    finally:
        test_script.unlink()


async def test_process_info():
    """Test process information"""
    print("\n=== Testing Process Information ===")
    
    manager = ProcessManager()
    
    # Create a long-running process
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("#!/usr/bin/env python3\n")
        f.write("import time\n")
        f.write("time.sleep(2)\n")
        test_script = Path(f.name)
    
    try:
        # Create process
        await manager.create_process(
            process_id="test_process",
            script_path=test_script,
            args=[]
        )
        
        # Get process info
        info = manager.get_all_process_info()
        print(f"Process info: {info}")
        
        assert "test_process" in info
        assert info["test_process"]["pid"] is not None
        assert info["test_process"]["running"] is True
        
        # Get running count
        count = manager.get_running_process_count()
        print(f"Running processes: {count}")
        assert count == 1
        
        # Stop process
        success = await manager.stop_process("test_process")
        assert success
        
        print("PASS: Process information test")
        
    finally:
        test_script.unlink()


async def test_process_stop():
    """Test process stop"""
    print("\n=== Testing Process Stop ===")
    
    manager = ProcessManager()
    
    # Create a long-running process
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("#!/usr/bin/env python3\n")
        f.write("import time\n")
        f.write("while True:\n")
        f.write("    time.sleep(1)\n")
        test_script = Path(f.name)
    
    try:
        # Create process
        await manager.create_process(
            process_id="test_process",
            script_path=test_script,
            args=[]
        )
        
        assert manager.is_process_running("test_process")
        
        # Stop process gracefully
        success = await manager.stop_process("test_process", timeout=5)
        print(f"Graceful stop success: {success}")
        assert success
        
        # Cleanup
        manager.cleanup_finished_processes()
        
        print("PASS: Process stop test")
        
    finally:
        test_script.unlink()


async def test_convenience_functions():
    """Test convenience functions"""
    print("\n=== Testing Convenience Functions ===")
    
    # Reset global manager
    reset_process_manager()
    
    project_root = Path.cwd()
    
    # Test start_ai_loop (without actually starting)
    # We'll just verify the function signature and imports work
    print("Convenience functions imported successfully")
    
    # Test global manager
    manager = get_process_manager()
    assert manager is not None
    assert isinstance(manager, ProcessManager)
    
    print("PASS: Convenience functions test")


async def test_multiple_processes():
    """Test multiple processes"""
    print("\n=== Testing Multiple Processes ===")
    
    manager = ProcessManager()
    
    # Create multiple test scripts
    test_scripts = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("import time\n")
            f.write(f"time.sleep({i + 1})\n")
            test_scripts.append(Path(f.name))
    
    try:
        # Create multiple processes
        for i, script in enumerate(test_scripts):
            await manager.create_process(
                process_id=f"process_{i}",
                script_path=script,
                args=[]
            )
        
        # Check running count
        count = manager.get_running_process_count()
        print(f"Running processes: {count}")
        assert count == 3
        
        # Get all info
        info = manager.get_all_process_info()
        assert len(info) == 3
        
        # Stop all processes
        results = await manager.stop_all_processes(timeout=5)
        print(f"Stop results: {results}")
        
        # Verify all stopped
        assert all(results.values())
        
        print("PASS: Multiple processes test")
        
    finally:
        for script in test_scripts:
            script.unlink()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Starting tests for process manager")
    print("=" * 60)
    
    try:
        await test_process_manager_creation()
        await test_process_creation()
        await test_process_info()
        await test_process_stop()
        await test_convenience_functions()
        await test_multiple_processes()
        
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
