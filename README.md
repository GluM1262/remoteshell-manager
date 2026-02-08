# RemoteShell Manager

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

## Description

RemoteShell Manager is a client-server application for remote execution of commands on Linux devices in real-time mode.

## Technology Stack

- Python 3.9 or higher
- Linux operating system (for server)
- Network connectivity between client and server

## 🏗️ Project Structure
## Project Structure

```
remoteshell-manager/
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
├── shared/                 # Shared components
└── docker-compose.yml     # Docker configuration
```

## Installation and Setup

Instructions will be added in the following commits.

## License

**Made with ❤️ for the Linux community**