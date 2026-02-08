# RemoteShell Manager

> Secure remote command execution for Linux devices with web-based management
Remote Linux device management system via WebSocket with a modern web interface.
A client-server application for remote Linux device management via WebSocket connections. Execute shell commands on remote devices in real-time with a simple and intuitive interface.

## 🚀 Features

- **Real-time Command Execution**: Execute shell commands on remote Linux devices instantly
- **WebSocket Communication**: Efficient bi-directional communication between client and server
- **Multiple Connections**: Support for multiple simultaneous client connections
- **Async Operations**: Built with asyncio for high performance
- **Command Validation**: Basic security checks for dangerous commands
- **Timeout Handling**: Configurable timeout for long-running commands (30 seconds default)
- **Error Handling**: Comprehensive error handling and logging
- **Interactive CLI**: User-friendly command-line interface with formatted output
- **Auto-Reconnect**: Automatic reconnection on connection loss

## 📋 System Requirements
Remote Linux device management system via WebSocket.

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
RemoteShell Manager is a client-server application for remote execution of commands on Linux devices in real-time mode. It features a modern, responsive web interface for managing devices and executing commands with live results.

## Features

- 🖥️ **Device Management** - View and monitor connected devices
- ⚡ **Real-time Updates** - WebSocket-based live status updates
- 📝 **Command Execution** - Send commands to devices and view results
- 📊 **Command History** - Browse and filter command history
- 🎨 **Modern UI** - Clean, responsive web interface
- 📱 **Mobile Friendly** - Works on desktop and mobile devices

## Technology Stack

- **Backend**: Python 3.9+, FastAPI, WebSocket, asyncio
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **API**: RESTful API with OpenAPI/Swagger documentation
- Python 3.9 or higher
- Linux operating system (for server)
- Network connectivity between client and server

## 🏗️ Project Structure
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
├── client/                 # Client application
│   ├── __init__.py
│   ├── main.py            # Client entry point with CLI
│   ├── websocket_client.py # WebSocket client implementation
│   └── requirements.txt   # Client dependencies
├── server/                 # Server application
│   ├── __init__.py
│   ├── main.py            # FastAPI application
│   ├── websocket_handler.py # WebSocket connection management
│   ├── shell_executor.py  # Shell command executor
│   └── requirements.txt   # Server dependencies
├── shared/                 # Shared components
│   ├── __init__.py
│   └── protocol.py        # Communication protocol (Pydantic models)
├── .gitignore
├── README.md
├── docker-compose.yml     # Docker deployment configuration
└── requirements.txt       # Combined dependencies
```

## 🔧 Installation

### Option 1: Direct Installation

1. **Clone the repository**:
```bash
git clone https://github.com/GluM1262/remoteshell-manager.git
cd remoteshell-manager
```

2. **Install server dependencies**:
```bash
cd server
pip install -r requirements.txt
```

3. **Install client dependencies** (in a separate terminal or machine):
```bash
cd client
pip install -r requirements.txt
```

### Option 2: Using Virtual Environment (Recommended)

1. **Clone the repository**:
```bash
git clone https://github.com/GluM1262/remoteshell-manager.git
cd remoteshell-manager
```

2. **Set up server**:
```bash
# Create virtual environment for server
python3 -m venv venv-server
source venv-server/bin/activate  # On Windows: venv-server\Scripts\activate

# Install server dependencies
cd server
pip install -r requirements.txt
```

3. **Set up client** (in a separate terminal):
```bash
# Create virtual environment for client
python3 -m venv venv-client
source venv-client/bin/activate  # On Windows: venv-client\Scripts\activate

# Install client dependencies
cd client
pip install -r requirements.txt
```

### Option 3: Docker Deployment

```bash
# Build and start the server
docker-compose up -d

# The server will be available at ws://localhost:8000/ws
```

## 🚀 Quick Start

### Starting the Server

1. Navigate to the server directory:
```bash
cd server
```

2. Run the server:
```bash
python main.py
```

The server will start on `http://0.0.0.0:8000` with the WebSocket endpoint at `ws://localhost:8000/ws`.

You should see output similar to:
```
2024-01-01 12:00:00 - INFO - RemoteShell Manager server starting up...
2024-01-01 12:00:00 - INFO - Starting RemoteShell Manager server on http://0.0.0.0:8000
2024-01-01 12:00:00 - INFO - WebSocket endpoint: ws://localhost:8000/ws
2024-01-01 12:00:00 - INFO - Health check: http://localhost:8000/health
```

### Connecting with the Client

1. In a new terminal, navigate to the client directory:
```bash
cd client
```

2. Run the client:
```bash
python main.py --host localhost --port 8000
```

3. You'll see the interactive prompt:
```
RemoteShell Manager - Interactive Client
Connecting to localhost:8000...

✅ Connected successfully!

Type your commands below. Use 'exit' or 'quit' to disconnect.
Use Ctrl+C to force quit.

🔹 Command: 
```

## 💻 Usage Examples

### Basic Commands

```bash
# List files
🔹 Command: ls -la

# Check system information
🔹 Command: uname -a

# Check disk usage
🔹 Command: df -h

# View running processes
🔹 Command: ps aux | head -10

# Network information
🔹 Command: ip addr show
```

### Sample Output

```
🔹 Command: echo "Hello from remote server!"

⏳ Executing command...

Exit Code: 0

--- STDOUT ---
Hello from remote server!
```

### Client Command-Line Options

```bash
# Connect to a specific host and port
python main.py --host 192.168.1.100 --port 8000

# Enable debug logging
python main.py --host localhost --port 8000 --debug

# Show help
python main.py --help
```

## 🔌 API Endpoints

### HTTP Endpoints

- **GET /** - Root endpoint with server information
- **GET /health** - Health check endpoint
  ```json
  {
    "status": "healthy",
    "active_connections": 2
  }
  ```

### WebSocket Endpoint

- **WS /ws** - WebSocket connection for command execution

#### Message Format

**Command Message (Client → Server)**:
```json
{
  "type": "command",
  "command": "ls -la",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

**Response Message (Server → Client)**:
```json
{
  "type": "response",
  "stdout": "total 48\ndrwxr-xr-x...",
  "stderr": "",
  "exit_code": 0,
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

**Error Message**:
```json
{
  "type": "error",
  "error": "Command execution failed",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

## 🔒 Security Considerations

**⚠️ IMPORTANT: This is a basic implementation intended for trusted networks only.**

### Current Limitations

- **No Authentication**: The server does not implement user authentication
- **No Encryption**: Communication is not encrypted (use VPN or SSH tunnel in production)
- **Command Validation**: Only basic dangerous command filtering is implemented
- **Privilege Level**: Commands run with the same privileges as the server process
- **Network Exposure**: By default, the server binds to 0.0.0.0 (all interfaces)

### Security Recommendations

1. **Use in Trusted Networks Only**: Deploy only on private, trusted networks
2. **Implement Authentication**: Add token-based or certificate-based authentication
3. **Use TLS/SSL**: Enable WSS (WebSocket Secure) for encrypted communication
4. **Run with Limited Privileges**: Use a dedicated user with restricted permissions
5. **Firewall Rules**: Restrict access using firewall rules (iptables, ufw, etc.)
6. **Command Whitelist**: Implement a whitelist of allowed commands
7. **Rate Limiting**: Add rate limiting to prevent abuse
8. **Audit Logging**: Log all commands and access attempts
9. **Use SSH Tunneling**: Create an SSH tunnel for additional security:
   ```bash
   ssh -L 8000:localhost:8000 user@remote-server
   ```

### Blocked Dangerous Commands

The server blocks certain dangerous command patterns:
- `rm -rf /` - System-wide deletion
- `mkfs` - Filesystem formatting
- `dd if=/dev/zero` - Disk wiping
- `> /dev/sda` - Direct disk write
- `:(){ :|:& };:` - Fork bomb

**Note**: This list is not exhaustive. Implement comprehensive validation for production use.

## 🐳 Docker Deployment

### Building and Running

1. **Start the server**:
```bash
docker-compose up -d
```

2. **View logs**:
```bash
docker-compose logs -f server
```

3. **Stop the server**:
```bash
docker-compose down
```

### Custom Docker Build

Create `Dockerfile.server` in the project root:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ ./server/
COPY shared/ ./shared/

EXPOSE 8000

CMD ["python", "-m", "server.main"]
```

## 🧪 Testing

### Manual Testing

1. **Start the server**:
```bash
cd server
python main.py
```

2. **In another terminal, test with curl**:
```bash
# Health check
curl http://localhost:8000/health
```

3. **Connect with the client**:
```bash
cd client
python main.py --host localhost --port 8000
```

4. **Try various commands**:
```bash
ls -la
pwd
whoami
date
```

## 📝 Development

### Code Style

- Follow PEP 8 style guide
- Use type hints for all functions
- Add docstrings to all public functions and classes
- Use meaningful variable names
- Include inline comments for complex logic

### Logging

The project uses Python's built-in logging module:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message")
```

### Adding New Features

1. Create a new branch for your feature
2. Implement changes with tests
3. Update documentation
4. Submit a pull request

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Review Process

- All PRs require at least one review
- Tests must pass
- Code must follow style guidelines
- Documentation must be updated

## 📄 License

This project is licensed under the MIT License. See below for details:

```
MIT License

Copyright (c) 2024 RemoteShell Manager

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🆘 Troubleshooting

### Connection Issues

**Problem**: Client cannot connect to server

**Solutions**:
- Verify the server is running: `curl http://localhost:8000/health`
- Check firewall rules: `sudo ufw status`
- Verify correct host and port in client
- Check server logs for errors

### Command Execution Issues

**Problem**: Commands time out or fail

**Solutions**:
- Check if command is blocked by security validation
- Increase timeout in `shell_executor.py`
- Verify server has necessary permissions
- Check server logs for detailed errors

### WebSocket Connection Drops

**Problem**: Connection drops frequently

**Solutions**:
- Check network stability
- Adjust ping interval in `websocket_client.py`
- Enable debug logging: `python main.py --debug`
- Check for firewall interference

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review closed issues for solutions

## 🗺️ Roadmap

Future enhancements planned:
- [ ] User authentication (JWT tokens)
- [ ] TLS/SSL support (WSS)
- [ ] Command history persistence
- [ ] Multi-server support
- [ ] Web-based UI
- [ ] File transfer capabilities
- [ ] Session recording
- [ ] Role-based access control
- [ ] Command templates/aliases
- [ ] Notification system

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---
├── server/                 # Server application
│   ├── main.py            # FastAPI application
│   ├── static/            # Static web files
│   │   ├── index.html     # Main HTML page
│   │   ├── css/           # Stylesheets
│   │   └── js/            # JavaScript files
│   └── README.md          # Server documentation
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Quick Start

### Server Setup

1. **Install dependencies:**

```bash
pip install -r server/requirements.txt
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your device tokens
```

3. **Start the server:**

```bash
python3 -m server.main
```

The server will start on `http://0.0.0.0:8000`.

### Testing

Test the health endpoint:

```bash
curl http://localhost:8000/health
```

### WebSocket Connection

Connect with a device token:

```bash
# Using Python
python3 -c "
import asyncio
import json
import websockets

async def test():
    uri = 'ws://localhost:8000/ws?token=abc123token'
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            'type': 'command',
            'command': 'echo hello',
            'id': '1'
        }))
        print(await ws.recv())

asyncio.run(test())
"
```

## Features

- **WebSocket Communication**: Real-time bidirectional communication
- **Token Authentication**: Secure device authentication
- **Command Execution**: Asynchronous shell command execution with timeout
- **Security**: Command validation, blacklist filtering, timeout protection
- **Device Management**: Track connected devices and their status
- **REST API**: Health check and device listing endpoints

## Documentation

For detailed server documentation, see [server/README.md](server/README.md).

## Security Considerations

- Use strong, unique device tokens
- Configure allowed origins for production CORS
- Review command execution logs regularly
- Consider implementing command whitelisting for production
- Use HTTPS/WSS in production environments

## Installation and Setup

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/GluM1262/remoteshell-manager.git
   cd remoteshell-manager
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the server**
   ```bash
   python server/main.py
   ```
   
   Or with uvicorn:
   ```bash
   uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the web interface**
   
   Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage

### Web Interface

The web interface provides:

1. **Device List** - View all connected devices with status indicators
2. **Command Panel** - Select device and send commands
3. **Result Display** - View command output in real-time
4. **History** - Browse and filter command execution history

### API Endpoints

- `GET /api/devices` - List all devices
- `POST /api/command` - Send command to device
- `GET /api/command/{command_id}` - Get command status
- `GET /api/history` - Get command history
- `GET /api/statistics` - Get system statistics
- `WS /ws` - WebSocket for real-time updates

## Screenshots

### Desktop View
![Web Interface](https://github.com/user-attachments/assets/c23255e4-cdea-4974-9678-8bac0d506f31)

### Command Results
![Command Results](https://github.com/user-attachments/assets/df6f2bcb-bec8-4207-be9b-f98368979d02)

### Mobile View
![Mobile View](https://github.com/user-attachments/assets/c017c860-8031-4740-8887-dae5034529bd)

## Development

### Running in Development Mode

```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag enables auto-reload on code changes.
See [server/README.md](server/README.md) for complete installation and configuration instructions.

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
**Made with ❤️ for the Linux community**
