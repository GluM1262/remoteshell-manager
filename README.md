# RemoteShell Manager

Remote Linux device management system via WebSocket with enterprise-grade security features.

## Description

RemoteShell Manager is a secure client-server application for remote execution of commands on Linux devices in real-time mode. Built with security-first principles, it provides essential features like command whitelisting, execution timeouts, TLS encryption, and non-root execution.

## Technology Stack

- Python 3.9+
- FastAPI
- WebSocket
- asyncio
- TLS/SSL (cryptography, pyOpenSSL)

## Security Features

🔒 **Four Core Security Layers:**

1. **Non-Root Execution** - Client runs as unprivileged user
2. **Command Whitelist** - Strict control over allowed commands
3. **Execution Timeout** - Automatic termination of long-running commands
4. **TLS Encryption** - Secure WebSocket communication (WSS)

Additional protections:
- Command blacklist (dangerous operations always blocked)
- Shell operator restrictions
- Command length limits
- Comprehensive audit logging

## Project Structure

```
remoteshell-manager/
├── server/                 # Server application
│   ├── main.py            # FastAPI server with TLS
│   ├── security.py        # Security manager
│   ├── config.py          # Configuration
│   ├── tls/               # TLS certificates
│   └── requirements.txt
├── client/                # Client application
│   ├── websocket_client.py    # WebSocket client with TLS
│   ├── command_executor.py    # Command executor with security
│   ├── config.yaml.example    # Configuration template
│   └── requirements.txt
├── tests/                 # Security tests
├── docs/                  # Documentation
│   └── SECURITY.md       # Comprehensive security guide
└── SETUP.md              # Quick setup guide
```

## Quick Start

### 1. Server Setup

```bash
cd server
pip install -r requirements.txt
cd tls && ./generate_certs.sh && cd ..
cp .env.example .env
python main.py
```

### 2. Client Setup

```bash
cd client
pip install -r requirements.txt
cp config.yaml.example config.yaml
# Edit config.yaml with your server URL and token
python websocket_client.py
```

### 3. Run Tests

```bash
python3 tests/test_security.py
python3 tests/test_command_executor.py
```

## Configuration

### Server Configuration (`.env`)

```bash
USE_TLS=true                        # Enable TLS encryption
ENABLE_COMMAND_WHITELIST=true       # Enable command whitelist
MAX_EXECUTION_TIME=30               # Command timeout in seconds
ALLOW_SHELL_OPERATORS=false         # Block shell operators
```

### Client Configuration (`config.yaml`)

```yaml
server:
  url: "wss://your-server:8000/ws"
  use_ssl: true

security:
  validate_ssl: true
  enable_whitelist: true
  max_execution_time: 30
  allow_shell_operators: false
```

## Documentation

- **[Setup Guide](SETUP.md)** - Detailed installation and configuration
- **[Security Guide](docs/SECURITY.md)** - Comprehensive security documentation
- **[TLS Configuration](server/tls/README.md)** - Certificate management

## Production Deployment

⚠️ **Security Checklist for Production:**

- [ ] Run client as non-root user (`remoteshell`)
- [ ] Enable TLS with trusted certificates (Let's Encrypt)
- [ ] Enable command whitelist with minimal safe commands
- [ ] Set execution timeout (recommended: 30s)
- [ ] Disable shell operators
- [ ] Use strong authentication tokens (32+ characters)
- [ ] Configure firewall rules
- [ ] Set file permissions (600 for configs)
- [ ] Enable SSL certificate validation
- [ ] Set up log monitoring

See [SECURITY.md](docs/SECURITY.md) for complete security best practices.

## Testing

All security features include automated tests:

```bash
# Test security manager
python3 tests/test_security.py

# Test command executor
python3 tests/test_command_executor.py
```

## License

MIT