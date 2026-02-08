#!/usr/bin/env python3
"""
Test script for command executor security checks.
"""

import sys
import os
import asyncio

# Add client directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'client'))


class MockConfig:
    """Mock configuration for testing."""
    class Security:
        enable_whitelist = False
        allowed_commands = ["ls", "pwd", "whoami"]
        blocked_commands = ["rm -rf /", "mkfs"]
        max_execution_time = 5
        max_command_length = 100
        allow_shell_operators = False
    
    def __init__(self):
        self.security = self.Security()


async def test_command_executor():
    """Test command executor security checks."""
    from command_executor import CommandExecutor
    
    print("=" * 60)
    print("Testing CommandExecutor Security")
    print("=" * 60)
    
    # Test 1: Basic command execution
    print("\n1. Testing basic command execution:")
    config = MockConfig()
    executor = CommandExecutor(config)
    
    result = await executor.execute("echo 'Hello World'")
    print(f"  ✅ Command executed: echo")
    print(f"    stdout: {result['stdout'].strip()}")
    print(f"    exit_code: {result['exit_code']}")
    
    # Test 2: Blocked command
    print("\n2. Testing blocked commands:")
    result = await executor.execute("rm -rf /test")
    status = "✅ PASS" if result['exit_code'] == -1 else "❌ FAIL"
    print(f"  {status}: Blocked dangerous command")
    print(f"    stderr: {result['stderr']}")
    
    # Test 3: Shell operators
    print("\n3. Testing shell operators (disabled):")
    result = await executor.execute("echo hello && echo world")
    status = "✅ PASS" if result['exit_code'] == -1 else "❌ FAIL"
    print(f"  {status}: Blocked shell operators")
    print(f"    stderr: {result['stderr']}")
    
    # Test 4: Timeout
    print("\n4. Testing command timeout:")
    print("  Running 'sleep 10' with 2s timeout...")
    result = await executor.execute("sleep 10", timeout=2)
    status = "✅ PASS" if "timed out" in result['stderr'] else "❌ FAIL"
    print(f"  {status}: Command timed out as expected")
    print(f"    stderr: {result['stderr']}")
    print(f"    execution_time: {result['execution_time']:.2f}s")
    
    # Test 5: Whitelist mode
    print("\n5. Testing whitelist mode:")
    config.security.enable_whitelist = True
    executor = CommandExecutor(config)
    
    result = await executor.execute("ls")
    status = "✅ PASS" if result['exit_code'] != -1 else "❌ FAIL"
    print(f"  {status}: Whitelisted command allowed")
    
    result = await executor.execute("cat /etc/passwd")
    status = "✅ PASS" if result['exit_code'] == -1 else "❌ FAIL"
    print(f"  {status}: Non-whitelisted command blocked")
    print(f"    stderr: {result['stderr']}")
    
    # Test 6: Command length limit
    print("\n6. Testing command length limit:")
    long_command = "echo " + "a" * 200
    result = await executor.execute(long_command)
    status = "✅ PASS" if "exceeds maximum length" in result['stderr'] else "❌ FAIL"
    print(f"  {status}: Long command blocked")
    print(f"    stderr: {result['stderr']}")
    
    print("\n" + "=" * 60)
    print("CommandExecutor tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_command_executor())
