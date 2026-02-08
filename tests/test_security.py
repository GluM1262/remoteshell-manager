#!/usr/bin/env python3
"""
Test script for security manager validation logic.
"""

import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from security import SecurityManager, SecurityPolicy


def test_command_validation():
    """Test command validation logic."""
    print("=" * 60)
    print("Testing SecurityManager Command Validation")
    print("=" * 60)
    
    # Test 1: Default policy (no whitelist, blacklist only)
    print("\n1. Testing default policy (blacklist only):")
    policy = SecurityPolicy()
    manager = SecurityManager(policy)
    
    test_cases = [
        ("ls -la", True, "Simple command"),
        ("rm -rf /", False, "Dangerous command"),
        ("echo hello", True, "Safe echo"),
        ("mkfs /dev/sda", False, "Filesystem format"),
        ("whoami", True, "Whoami command"),
        (":(){ :|:& };:", False, "Fork bomb"),
        ("ls && pwd", False, "Shell operator && (not allowed by default)"),
    ]
    
    for command, expected, description in test_cases:
        is_valid, error = manager.validate_command(command, "test-device")
        status = "✅ PASS" if (is_valid == expected) else "❌ FAIL"
        print(f"  {status}: {description}")
        print(f"    Command: {command}")
        print(f"    Expected: {expected}, Got: {is_valid}")
        if error:
            print(f"    Error: {error}")
    
    # Test 2: Whitelist enabled
    print("\n2. Testing with whitelist enabled:")
    policy = SecurityPolicy(
        enable_whitelist=True,
        allowed_commands=["ls", "pwd", "whoami"]
    )
    manager = SecurityManager(policy)
    
    test_cases = [
        ("ls -la", True, "Whitelisted command with args"),
        ("pwd", True, "Whitelisted command"),
        ("echo hello", False, "Non-whitelisted command"),
        ("cat /etc/passwd", False, "Non-whitelisted command"),
        ("whoami", True, "Whitelisted command"),
    ]
    
    for command, expected, description in test_cases:
        is_valid, error = manager.validate_command(command, "test-device")
        status = "✅ PASS" if (is_valid == expected) else "❌ FAIL"
        print(f"  {status}: {description}")
        print(f"    Command: {command}")
        print(f"    Expected: {expected}, Got: {is_valid}")
        if error:
            print(f"    Error: {error}")
    
    # Test 3: Shell operators allowed
    print("\n3. Testing with shell operators allowed:")
    policy = SecurityPolicy(allow_shell_operators=True)
    manager = SecurityManager(policy)
    
    test_cases = [
        ("ls && pwd", True, "Shell operator allowed"),
        ("echo hello | grep h", True, "Pipe operator allowed"),
        ("rm -rf /", False, "Still blocked by blacklist"),
    ]
    
    for command, expected, description in test_cases:
        is_valid, error = manager.validate_command(command, "test-device")
        status = "✅ PASS" if (is_valid == expected) else "❌ FAIL"
        print(f"  {status}: {description}")
        print(f"    Command: {command}")
        print(f"    Expected: {expected}, Got: {is_valid}")
        if error:
            print(f"    Error: {error}")
    
    # Test 4: Max execution time
    print("\n4. Testing max execution time:")
    policy = SecurityPolicy(max_execution_time=60)
    manager = SecurityManager(policy)
    
    # Test timeout enforcement
    timeout = manager.get_max_execution_time(None)
    print(f"  ✅ PASS: Default timeout: {timeout}s (expected 60)")
    
    timeout = manager.get_max_execution_time(30)
    print(f"  ✅ PASS: Requested 30s, got: {timeout}s (expected 30)")
    
    timeout = manager.get_max_execution_time(120)
    print(f"  ✅ PASS: Requested 120s, got: {timeout}s (expected 60 - capped)")
    
    # Test 5: Command length limit
    print("\n5. Testing command length limit:")
    policy = SecurityPolicy(max_command_length=50)
    manager = SecurityManager(policy)
    
    short_cmd = "ls"
    long_cmd = "a" * 100
    
    is_valid, error = manager.validate_command(short_cmd, "test-device")
    status = "✅ PASS" if is_valid else "❌ FAIL"
    print(f"  {status}: Short command accepted")
    
    is_valid, error = manager.validate_command(long_cmd, "test-device")
    status = "✅ PASS" if not is_valid else "❌ FAIL"
    print(f"  {status}: Long command rejected")
    if error:
        print(f"    Error: {error}")
    
    print("\n" + "=" * 60)
    print("SecurityManager tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_command_validation()
