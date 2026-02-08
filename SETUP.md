# RemoteShell Manager - Setup Guide

Quick start guide for setting up RemoteShell Manager with security features.

## Server Setup

### 1. Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

### 2. Generate TLS Certificates

```bash
cd server/tls
./generate_certs.sh
```

### 3. Configure Server

Copy the example environment file and edit:

```bash
cd server
cp .env.example .env
```

Edit `.env` and set:

```bash
# Enable TLS for production
USE_TLS=true

# Enable command whitelist for production
ENABLE_COMMAND_WHITELIST=true

# Set execution timeout
MAX_EXECUTION_TIME=30

# Disable shell operators for security
ALLOW_SHELL_OPERATORS=false
```

### 4. Run Server

```bash
cd server
python main.py
```

The server will start on `http://localhost:8000` (or `https://` if TLS is enabled).

## Client Setup

### 1. Install Dependencies

```bash
cd client
pip install -r requirements.txt
```

### 2. Configure Client

Copy the example config and edit:

```bash
cd client
cp config.yaml.example config.yaml
```

Edit `config.yaml` and set:

```yaml
server:
  url: "wss://your-server:8000/ws"  # Use wss:// for TLS
  token: "your-device-token-here"
  use_ssl: true

security:
  validate_ssl: true  # Set to false for self-signed certs (dev only)
  enable_whitelist: true  # Enable for production
  max_execution_time: 30
  allow_shell_operators: false
```

### 3. Run Client

```bash
cd client
python websocket_client.py
```

## Security Configuration

### Non-Root Execution

**Important:** Always run the client as a non-root user:

```bash
# Create dedicated user
sudo useradd -r -s /bin/bash remoteshell

# Run client as this user
sudo -u remoteshell python client/websocket_client.py
```

### Command Whitelist

For production, enable strict whitelist mode:

**Server** (`.env`):
```bash
ENABLE_COMMAND_WHITELIST=true
ALLOWED_COMMANDS=ls,pwd,whoami,hostname,uptime,df,free,ps,systemctl status
```

**Client** (`config.yaml`):
```yaml
security:
  enable_whitelist: true
  allowed_commands:
    - "ls"
    - "pwd"
    - "whoami"
    - "hostname"
```

### TLS Encryption

For production, always use TLS:

1. Generate production certificates (Let's Encrypt recommended)
2. Enable TLS in server config: `USE_TLS=true`
3. Use `wss://` URL in client config
4. Enable SSL validation: `validate_ssl: true`

### Execution Timeout

Prevent long-running commands:

```bash
# Server
MAX_EXECUTION_TIME=30

# Client
security:
  max_execution_time: 30
```

## Testing

Run security tests:

```bash
# Test security manager
python3 tests/test_security.py

# Test command executor
python3 tests/test_command_executor.py
```

## Production Checklist

Before deploying to production:

- [ ] Generate production TLS certificates (Let's Encrypt)
- [ ] Enable TLS encryption (`USE_TLS=true`)
- [ ] Enable command whitelist (`ENABLE_COMMAND_WHITELIST=true`)
- [ ] Configure minimal whitelist of safe commands
- [ ] Set execution timeout (30s recommended)
- [ ] Disable shell operators (`ALLOW_SHELL_OPERATORS=false`)
- [ ] Run client as non-root user
- [ ] Set config file permissions to 600
- [ ] Use strong authentication tokens (32+ characters)
- [ ] Enable SSL certificate validation
- [ ] Configure firewall rules
- [ ] Set up log monitoring

## Documentation

- **Security Guide**: See `docs/SECURITY.md` for comprehensive security documentation
- **TLS Setup**: See `server/tls/README.md` for TLS configuration details

## Support

For security issues or questions, refer to the security documentation or contact your system administrator.
