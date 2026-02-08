# RemoteShell Manager - Testing Guide

## Overview

This guide covers how to test RemoteShell Manager components, run integration tests, and verify your installation.

## Prerequisites

- Python 3.9 or higher
- All dependencies installed (`pip3 install -r server/requirements.txt -r client/requirements.txt`)
- Server and client configured

## Quick Validation

Run the validation script to check your installation:

```bash
./validate.sh
```

This checks:
- Python version
- Dependencies
- File structure
- Configuration files
- TLS certificates
- Module imports
- Basic tests

## Unit Tests

### Security Manager Tests

Tests command validation, whitelist, blacklist, and security policies:

```bash
python3 tests/test_security.py
```

Expected output:
```
✅ All security manager tests passing
- Blacklist validation
- Whitelist validation  
- Shell operator blocking
- Timeout enforcement
- Command length limits
```

### Command Executor Tests

Tests command execution with security controls:

```bash
python3 tests/test_command_executor.py
```

**Note**: Some tests may take time due to timeout testing.

## Integration Testing

### 1. Server Startup Test

Start the server and verify it runs without errors:

```bash
cd server
python3 main.py
```

Expected output:
```
RemoteShell Manager Server Starting
...
Database initialized
Server startup complete
Uvicorn running on http://0.0.0.0:8000
```

Test the health endpoint:

```bash
curl http://localhost:8000/
```

Expected: JSON response with `"status": "running"`

### 2. Web Interface Test

With server running, open browser to:

```
http://localhost:8000/web
```

Verify:
- Page loads without errors (check browser console)
- Server status shows "Online"
- Navigation works
- No JavaScript errors

### 3. REST API Test

Test API endpoints:

```bash
# Health check
curl http://localhost:8000/

# List devices
curl http://localhost:8000/api/devices

# View API documentation
open http://localhost:8000/docs
```

### 4. Client Connection Test

Start a client (in another terminal):

```bash
cd client
cp config.yaml.example config.yaml
# Edit config.yaml with server URL and token
python3 main.py
```

Expected output:
```
RemoteShell Manager Client Starting
...
Connecting to ws://localhost:8000/ws
Connected to server
Server welcome: Connected to RemoteShell Manager
```

Verify in server logs:
```
Device connected: device_abc123456
```

### 5. Command Execution Test

Send a command via API:

```bash
# Get device ID from server logs or API
DEVICE_ID="device_abc123456"

# Send command
curl -X POST "http://localhost:8000/api/devices/$DEVICE_ID/command?command=whoami"
```

Check client logs for command execution.

### 6. Command History Test

View command history:

```bash
curl http://localhost:8000/api/history
```

Should show executed commands with status and results.

### 7. Queue System Test

Test command queueing for offline devices:

1. Stop the client
2. Send command to offline device:
   ```bash
   curl -X POST "http://localhost:8000/api/devices/$DEVICE_ID/command?command=uptime"
   ```
3. Check response: `"status": "queued"`
4. Start client again
5. Verify command is sent automatically
6. Check history for command result

### 8. Security Features Test

#### Test Blacklist

Try dangerous command:

```bash
curl -X POST "http://localhost:8000/api/devices/$DEVICE_ID/command?command=rm%20-rf%20/"
```

Expected: `400 Bad Request` with "blocked by security policy"

#### Test Whitelist

Enable whitelist in server/.env:
```bash
ENABLE_COMMAND_WHITELIST=true
```

Restart server and try non-whitelisted command:

```bash
curl -X POST "http://localhost:8000/api/devices/$DEVICE_ID/command?command=vi%20test.txt"
```

Expected: `400 Bad Request` with "not in allowed whitelist"

#### Test Timeout

Send long-running command:

```bash
curl -X POST "http://localhost:8000/api/devices/$DEVICE_ID/command?command=sleep%2060&timeout=5"
```

Should timeout after 5 seconds.

### 9. TLS/SSL Test

Generate certificates:

```bash
cd server/tls
./generate_certs.sh
```

Enable TLS in server/.env:
```
USE_TLS=true
```

Update client config.yaml:
```yaml
server:
  url: "wss://localhost:8000/ws"
  use_ssl: true
security:
  validate_ssl: false  # For self-signed certs
```

Restart both and verify HTTPS/WSS connection.

## Automated Test Suite

Use the provided test scripts:

```bash
# Quick start and test
cd examples
./quickstart.sh

# Test commands
./test_commands.sh device_abc123456
```

## Performance Testing

### Load Test

Test with multiple clients:

```bash
# Start 10 clients
for i in {1..10}; do
    python3 client/main.py &
done
```

Monitor server performance and connection handling.

### Stress Test

Send many commands:

```bash
for i in {1..100}; do
    curl -X POST "http://localhost:8000/api/devices/$DEVICE_ID/command?command=echo%20test$i"
    sleep 0.1
done
```

Check all commands execute successfully.

## Troubleshooting

### Common Issues

#### ImportError

```
Solution: pip3 install -r server/requirements.txt -r client/requirements.txt
```

#### Connection Refused

```
Solution: 
1. Check server is running
2. Verify port 8000 is not blocked
3. Check firewall settings
```

#### Authentication Failed

```
Solution:
1. Verify token in server/.env matches client config.yaml
2. Check DEVICE_TOKENS environment variable
3. Review auth manager logs
```

#### Command Not Executing

```
Solution:
1. Check whitelist/blacklist settings
2. Review security manager logs
3. Verify command syntax
4. Check timeout settings
```

### Debug Mode

Enable debug logging:

**Server** (.env):
```
LOG_LEVEL=DEBUG
```

**Client** (config.yaml):
```yaml
logging:
  level: "DEBUG"
```

### Log Files

- Server logs: stdout or configure in uvicorn
- Client logs: `client/client.log` (if configured)
- Database: `server/remoteshell.db` (inspect with sqlite3)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r server/requirements.txt
          pip install -r client/requirements.txt
      - name: Run validation
        run: ./validate.sh
      - name: Run tests
        run: |
          python3 tests/test_security.py
```

## Manual Test Checklist

Before deployment:

- [ ] Server starts without errors
- [ ] Database initializes correctly
- [ ] Client connects successfully
- [ ] Commands execute properly
- [ ] Whitelist blocks non-allowed commands
- [ ] Blacklist blocks dangerous commands
- [ ] Timeouts enforced correctly
- [ ] Queue system works for offline devices
- [ ] Web interface loads and functions
- [ ] TLS encryption works (if enabled)
- [ ] Logs are generated correctly
- [ ] SystemD service starts (if configured)
- [ ] Non-root execution works
- [ ] All tests pass

## Security Testing

### Penetration Testing Checklist

- [ ] Test SQL injection in API parameters
- [ ] Test command injection via API
- [ ] Verify authentication token validation
- [ ] Test path traversal in file operations
- [ ] Verify TLS certificate validation
- [ ] Test XSS in web interface
- [ ] Verify CORS configuration
- [ ] Test rate limiting (if implemented)
- [ ] Verify sensitive data is not logged
- [ ] Test privilege escalation attempts

### Security Scan

Run with security analysis tools:

```bash
# Static analysis
bandit -r server/ client/

# Dependency vulnerabilities
safety check -r server/requirements.txt
safety check -r client/requirements.txt
```

## Support

For issues or questions:
1. Check this testing guide
2. Review logs for errors
3. Consult `docs/SECURITY.md` for security issues
4. Check `SETUP.md` for configuration help

## Contributing

When adding new features, ensure:
1. Unit tests are added
2. Integration tests are updated
3. Documentation is updated
4. validate.sh passes
5. Security review completed
