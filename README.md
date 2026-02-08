# RemoteShell Manager

> Secure remote command execution for Linux devices with web-based management

RemoteShell Manager is a production-ready client-server system for executing commands on remote Linux devices in real-time. Built with security-first principles, it features a web interface, REST API, command queue system, and multi-layer security controls.

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Web Interface](#web-interface)
  - [REST API](#rest-api)
  - [Command Line](#command-line)
- [Configuration](#configuration)
- [Security](#security-features)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

## Features

### Core Capabilities
- 🖥️ **Web Interface** - Manage devices and execute commands via browser
- 📡 **WebSocket Communication** - Real-time bidirectional messaging
- 📊 **REST API** - Full-featured API for automation
- 📝 **Command Queue** - Queue commands for offline devices
- 📚 **Command History** - Track all executed commands
- 🔄 **Auto Reconnection** - Clients automatically reconnect on disconnect

### Security Features
- 🔒 **Token Authentication** - Secure device authentication
- ✅ **Command Whitelist** - Restrict to approved commands only
- 🚫 **Command Blacklist** - Block dangerous operations
- ⏱️ **Timeout Enforcement** - Prevent long-running commands
- 🔐 **TLS Encryption** - Secure WebSocket (WSS) support
- 👤 **Non-Root Execution** - Run as unprivileged user
- 📋 **Audit Logging** - Track all security events

## How It Works

```
┌─────────────────┐         WebSocket/HTTPS        ┌─────────────────┐
│                 │◄──────────────────────────────►│                 │
│  Web Browser    │                                 │   FastAPI       │
│                 │         REST API                │   Server        │
└─────────────────┘                                 │                 │
                                                     │  • Database     │
┌─────────────────┐         WebSocket (WSS)        │  • Queue        │
│   Linux Client  │◄──────────────────────────────►│  • Auth         │
│                 │                                 │  • Security     │
│  • Executor     │                                 └─────────────────┘
│  • Reconnect    │
└─────────────────┘
```

**Flow:**
1. Server runs on a central machine (e.g., your laptop, cloud server)
2. Clients run on Linux devices you want to manage
3. Web interface or API sends commands to devices via server
4. Commands are validated, queued if device is offline, then executed
5. Results are stored and displayed in real-time

## Quick Start

### Automated Setup (Recommended)

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/GluM1262/remoteshell-manager.git
cd remoteshell-manager

# Run automated setup
cd examples
./quickstart.sh
```

This script will:
- ✅ Install Python dependencies
- ✅ Generate authentication token
- ✅ Configure server and client
- ✅ Provide start commands

Then in separate terminals:

```bash
# Terminal 1: Start the server
cd server
python3 main.py

# Terminal 2: Start a client
cd client
python3 main.py

# Terminal 3: Open web interface
# Visit http://localhost:8000/web in your browser
```

### Manual Setup

If you prefer manual control:

#### 1. Install Dependencies

```bash
pip3 install -r server/requirements.txt
pip3 install -r client/requirements.txt
```

#### 2. Configure Server

```bash
cd server
cp .env.example .env

# Generate secure token
TOKEN=$(openssl rand -hex 32)
echo "DEVICE_TOKENS=$TOKEN" >> .env

# Optional: Generate TLS certificates
cd tls && ./generate_certs.sh && cd ..
```

#### 3. Configure Client

```bash
cd client
cp config.yaml.example config.yaml

# Edit config.yaml - set server URL and token
nano config.yaml
```

#### 4. Start Components

```bash
# Terminal 1: Server
cd server && python3 main.py

# Terminal 2: Client  
cd client && python3 main.py
```

## Usage

### Web Interface

The easiest way to use RemoteShell Manager:

1. **Start the server** (see Quick Start above)
2. **Open browser** to `http://localhost:8000/web`
3. **View connected devices** in the devices table
4. **Send commands:**
   - Select device from dropdown
   - Enter command (e.g., `whoami`, `uptime`, `df -h`)
   - Click "Execute"
5. **View results** in the command history table

**Web Interface Features:**
- Real-time device status (online/offline)
- Command execution with timeout control
- Command history with filtering
- Device queue status
- Auto-refresh every 5 seconds

### REST API

Use the API for automation or integration:

#### List Devices

```bash
curl http://localhost:8000/api/devices
```

#### Send Command

```bash
# To online device - executes immediately
curl -X POST "http://localhost:8000/api/devices/DEVICE_ID/command?command=whoami"

# With timeout
curl -X POST "http://localhost:8000/api/devices/DEVICE_ID/command?command=uptime&timeout=10"

# To offline device - queues for later
curl -X POST "http://localhost:8000/api/devices/DEVICE_ID/command?command=ls"
# Returns: {"status": "queued", ...}
```

#### View Command History

```bash
# All devices
curl http://localhost:8000/api/history

# Specific device
curl http://localhost:8000/api/devices/DEVICE_ID/history

# With pagination
curl "http://localhost:8000/api/history?limit=50&offset=0"
```

#### Check Queue Status

```bash
curl http://localhost:8000/api/devices/DEVICE_ID/queue
```

#### API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Command Line

Use the test script for quick command testing:

```bash
cd examples

# Get device ID from server
curl http://localhost:8000/api/devices | python3 -m json.tool

# Run test commands
./test_commands.sh device_abc123456789
```

### Common Workflows

#### Remote System Monitoring

```bash
# Check disk space
curl -X POST "http://localhost:8000/api/devices/DEVICE_ID/command?command=df%20-h"

# Check memory usage
curl -X POST "http://localhost:8000/api/devices/DEVICE_ID/command?command=free%20-h"

# Check running processes
curl -X POST "http://localhost:8000/api/devices/DEVICE_ID/command?command=ps%20aux"

# System uptime
curl -X POST "http://localhost:8000/api/devices/DEVICE_ID/command?command=uptime"
```

#### Managing Offline Devices

When a device is offline, commands are automatically queued:

1. Send command to offline device → returns `"status": "queued"`
2. Device reconnects → queued commands execute automatically
3. Check queue: `GET /api/devices/DEVICE_ID/queue`
4. View results in history: `GET /api/devices/DEVICE_ID/history`

#### Batch Operations

Execute commands on multiple devices:

```bash
# Get all device IDs
DEVICES=$(curl -s http://localhost:8000/api/devices | jq -r '.devices[].device_id')

# Send command to each device
for device in $DEVICES; do
  curl -X POST "http://localhost:8000/api/devices/$device/command?command=whoami"
done
```

## Configuration

### Server Configuration (`.env`)

Create `server/.env` from `.env.example`:

```bash
# Server settings
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Authentication (comma-separated tokens)
DEVICE_TOKENS=your-secure-token-here,another-token

# TLS/SSL (optional but recommended for production)
USE_TLS=false
TLS_CERT_PATH=tls/cert.pem
TLS_KEY_PATH=tls/key.pem

# Security settings
ENABLE_COMMAND_WHITELIST=false  # Set true for production
MAX_EXECUTION_TIME=30
ALLOW_SHELL_OPERATORS=false

# Allowed commands (when whitelist enabled)
ALLOWED_COMMANDS=ls,pwd,whoami,hostname,uptime,df,du,free,ps
```

**Important Settings:**
- `DEVICE_TOKENS` - Authentication tokens for clients (required)
- `ENABLE_COMMAND_WHITELIST` - Enable for production (recommended)
- `USE_TLS` - Enable TLS encryption for production
- `MAX_EXECUTION_TIME` - Command timeout in seconds

### Client Configuration (`config.yaml`)

Create `client/config.yaml` from `config.yaml.example`:

```yaml
server:
  url: "ws://localhost:8000/ws"  # Use wss:// for TLS
  token: "your-secure-token-here"
  use_ssl: false
  reconnect_interval: 10
  ping_interval: 30

security:
  validate_ssl: true  # Set false for self-signed certs in dev
  enable_whitelist: false  # Set true for production
  allowed_commands:
    - "ls"
    - "pwd"
    - "whoami"
    - "hostname"
  max_execution_time: 30
  allow_shell_operators: false

logging:
  level: "INFO"
  file: "client.log"
```

**Key Settings:**
- `server.url` - WebSocket URL (ws:// or wss://)
- `server.token` - Must match server's DEVICE_TOKENS
- `security.enable_whitelist` - Enable for production
- `security.validate_ssl` - Set false for self-signed certs (dev only)

### Generating Secure Tokens

```bash
# For development
openssl rand -hex 16

# For production (more secure)
openssl rand -hex 32
```

### TLS Certificates

For development (self-signed):
```bash
cd server/tls
./generate_certs.sh
```

For production, use trusted certificates:
- Let's Encrypt (recommended)
- Commercial CA
- Internal PKI

See [server/tls/README.md](server/tls/README.md) for details.

## Security Features

### Multi-Layer Protection

1. **Token Authentication** ✅
   - Devices authenticate with secure tokens
   - Tokens loaded from environment variables
   - Failed attempts logged

2. **Command Whitelist** ✅
   - Optional strict mode (enabled/disabled)
   - Default safe commands provided
   - Customizable per deployment

3. **Command Blacklist** ✅
   - Always enforced dangerous command blocking
   - Prevents system damage: `rm -rf /`, `mkfs`, fork bombs
   - Blocks privilege escalation attempts

4. **Shell Operator Blocking** ✅
   - Blocks: `;`, `&&`, `||`, `|`, `>`, `<`, `$()`, backticks
   - Prevents command chaining
   - Prevents command injection

5. **Timeout Enforcement** ✅
   - Server-enforced maximum execution time
   - Automatic process termination
   - Prevents resource exhaustion

6. **TLS Encryption** ✅
   - TLS 1.2+ support
   - Secure cipher configuration
   - Optional for development, required for production

7. **Non-Root Execution** ✅
   - SystemD services run as unprivileged user
   - Capability restrictions
   - File system protections

### Security Best Practices

**For Development:**
- Self-signed certificates OK
- Whitelist optional
- Short tokens acceptable

**For Production:**
- ✅ Use TLS with trusted certificates
- ✅ Enable command whitelist
- ✅ Use strong tokens (32+ hex characters)
- ✅ Run as non-root user
- ✅ Enable firewall rules
- ✅ Monitor logs
- ✅ Regular security updates

See [SECURITY.md](docs/SECURITY.md) for complete security guide.

## Troubleshooting

### Server Issues

**Server won't start**
```bash
# Check Python version (requires 3.9+)
python3 --version

# Install dependencies
pip3 install -r server/requirements.txt

# Check if port 8000 is available
sudo netstat -tuln | grep 8000
# Or try a different port in .env

# Check logs for errors
cd server && python3 main.py
```

**Database errors**
```bash
# Remove and recreate database
rm server/remoteshell.db
cd server && python3 main.py
```

**Import errors**
```bash
# Reinstall dependencies
pip3 install --upgrade -r server/requirements.txt -r client/requirements.txt
```

### Client Issues

**Client can't connect**
```bash
# Verify server is running
curl http://localhost:8000/

# Check token matches in both configs
grep DEVICE_TOKENS server/.env
grep token client/config.yaml

# Verify WebSocket URL is correct
# ws:// for no TLS, wss:// for TLS
cat client/config.yaml | grep url

# Check network connectivity
ping your-server-address
```

**Authentication failed**
- Verify token in client config.yaml matches server .env
- Check DEVICE_TOKENS in server/.env (comma-separated for multiple)
- Ensure no extra spaces in tokens

**Commands not executing**

1. Check if command is whitelisted (if whitelist enabled):
   ```bash
   # Server .env
   ENABLE_COMMAND_WHITELIST=true
   ALLOWED_COMMANDS=ls,pwd,whoami
   ```

2. Check for dangerous commands (always blocked):
   - System commands: `rm -rf`, `mkfs`, `dd`
   - Shell operators: `&&`, `||`, `;`, `|`

3. Review client logs:
   ```bash
   tail -f client/client.log
   ```

4. Check server logs for security events

### Web Interface Issues

**Page won't load**
```bash
# Verify server is running
curl http://localhost:8000/

# Check browser console for JavaScript errors (F12)

# Try accessing API directly
curl http://localhost:8000/api/devices
```

**No devices showing**
- Ensure at least one client is connected
- Check client logs for connection status
- Refresh the page (auto-refresh is every 5 seconds)

**Commands not sending**
- Check device is online (green badge)
- Verify command is allowed by security policy
- Check browser console for errors (F12)

### Common Error Messages

| Error | Solution |
|-------|----------|
| `Connection refused` | Server not running or wrong URL |
| `Authentication failed` | Token mismatch between server and client |
| `Command blocked by security policy` | Command not in whitelist or in blacklist |
| `Command timed out` | Increase MAX_EXECUTION_TIME or command takes too long |
| `Port already in use` | Change PORT in server/.env or kill process using port |

### Getting Help

1. Check logs: `server/main.py` output and `client/client.log`
2. Review documentation: [TESTING.md](TESTING.md), [SECURITY.md](docs/SECURITY.md)
3. Run validation: `./validate.sh`
4. Check examples: `examples/README.md`

## Documentation

### Quick References
- **[SETUP.md](SETUP.md)** - Detailed setup guide
- **[TESTING.md](TESTING.md)** - Testing procedures and validation
- **[examples/README.md](examples/README.md)** - Example configurations and scripts

### Security & Compliance
- **[SECURITY.md](docs/SECURITY.md)** - Comprehensive security guide (6000+ words)
- **[SECURITY_SUMMARY.md](SECURITY_SUMMARY.md)** - Security analysis and compliance
- **[server/tls/README.md](server/tls/README.md)** - TLS certificate configuration

### Advanced Topics
- **[systemd/README.md](systemd/README.md)** - SystemD service installation
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Implementation details
- **[COMPLETION_REPORT.md](COMPLETION_REPORT.md)** - Project completion report

## Requirements

- **Python:** 3.9 or higher
- **Operating System:** Linux (server and clients)
- **Network:** TCP connectivity on port 8000 (configurable)
- **Optional:** OpenSSL for TLS certificates

## Technology Stack

- **Backend:** FastAPI, uvicorn
- **WebSocket:** websockets library
- **Database:** SQLite (file-based, no setup required)
- **Security:** cryptography, pyOpenSSL
- **Client:** Python asyncio, PyYAML

## Project Structure

```
remoteshell-manager/
├── server/                      # Server application
│   ├── main.py                 # FastAPI server with REST API
│   ├── database.py             # SQLite database operations
│   ├── queue_manager.py        # Command queue system
│   ├── auth.py                 # Token authentication
│   ├── security.py             # Security manager
│   ├── websocket_handler.py    # WebSocket handling
│   ├── static/                 # Web interface files
│   └── tls/                    # TLS certificates
├── client/                      # Client application
│   ├── main.py                 # Client entry point
│   ├── websocket_client.py     # WebSocket client
│   ├── command_executor.py     # Command execution
│   ├── config_manager.py       # Configuration
│   └── scripts/                # Installation scripts
├── examples/                    # Example configs and scripts
│   ├── quickstart.sh           # Automated setup
│   ├── server_config.env       # Server config example
│   └── client_config.yaml      # Client config example
├── tests/                       # Test suite
├── docs/                        # Documentation
└── systemd/                     # SystemD service files
```

## License

MIT

---

## Contributing

Contributions welcome! Please read [SECURITY.md](docs/SECURITY.md) before submitting security-related changes.

## Support

- 📖 Documentation: See `docs/` directory
- 🐛 Issues: Use GitHub Issues
- 💬 Questions: Check [TESTING.md](TESTING.md) for troubleshooting

---

**Production Status:** ✅ Ready for deployment  
**Security Scan:** ✅ 0 vulnerabilities (CodeQL)  
**Tests:** ✅ All passing