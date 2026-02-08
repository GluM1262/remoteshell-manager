# Security Tests

This directory contains test scripts for validating security features.

## Running Tests

### Security Manager Tests
Tests command validation, whitelist, blacklist, and security policies:

```bash
python3 tests/test_security.py
```

### Command Executor Tests
Tests client-side command execution with security controls:

```bash
python3 tests/test_command_executor.py
```

## Test Coverage

- ✅ Command blacklist validation
- ✅ Command whitelist validation
- ✅ Shell operator blocking
- ✅ Command length limits
- ✅ Execution timeout enforcement
- ✅ Security policy configuration

## Requirements

No additional requirements - tests use the same dependencies as the main application.
