# RemoteShell Manager Server

FastAPI-based WebSocket server for remote shell command execution with device token authentication.

## Features

- **WebSocket Communication**: Real-time bidirectional communication
- **Token-based Authentication**: Secure device authentication using tokens
- **Command Execution**: Asynchronous shell command execution with timeout
- **Security**: Command validation, blacklist filtering, and timeout protection
- **Device Management**: Track connected devices and their status
- **RESTful API**: Health check and device listing endpoints
- **Logging**: Comprehensive logging for monitoring and debugging

## Installation

### Requirements

- Python 3.9 or higher
- pip (Python package manager)

### Setup

1. **Install dependencies:**

```bash
cd server
pip install -r requirements.txt
```

2. **Configure environment:**

Copy the example environment file and edit it:

```bash
cp ../.env.example ../.env
```

Edit `.env` file with your configuration:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000

# Device Tokens (format: device_id:token,device_id:token)
DEVICE_TOKENS=device1:abc123token,device2:def456token,device3:ghi789token

# Command Execution
COMMAND_TIMEOUT=30
MAX_COMMAND_LENGTH=1000

# Logging
LOG_LEVEL=INFO
```

## Usage

### Starting the Server

**From server directory:**

```bash
python3 -m server.main
```

**From project root:**

```bash
cd /path/to/remoteshell-manager
python3 -m server.main
```

The server will start on `http://0.0.0.0:8000` by default.

### REST API Endpoints

#### Health Check

```bash
GET /health
```

Returns server health status and number of connected devices.

**Example:**

```bash
curl http://localhost:8000/health
```

**Response:**

```json
{
  "status": "healthy",
  "connected_devices": 2,
  "version": "1.0.0"
}
```

#### List Connected Devices

```bash
GET /devices
```

Returns list of all connected devices with their information.

**Example:**

```bash
curl http://localhost:8000/devices
```

**Response:**

```json
{
  "devices": [
    {
      "device_id": "device1",
      "connected_at": "2024-01-01T12:00:00",
      "last_command": "2024-01-01T12:05:00"
    }
  ],
  "count": 1
}
```

### WebSocket Endpoint

#### Connection

Connect to WebSocket endpoint with device token:

```
ws://localhost:8000/ws?token=YOUR_DEVICE_TOKEN
```

**Example with Python:**

```python
import asyncio
import json
import websockets

async def connect():
    uri = "ws://localhost:8000/ws?token=abc123token"
    async with websockets.connect(uri) as websocket:
        # Connection established
        print("Connected!")
        
        # Send command
        cmd = {
            "type": "command",
            "command": "ls -la",
            "id": "cmd_001"
        }
        await websocket.send(json.dumps(cmd))
        
        # Receive response
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(connect())
```

**Example with websocat:**

```bash
websocat "ws://localhost:8000/ws?token=abc123token"
```

Then send commands:

```json
{"type": "command", "command": "echo hello", "id": "1"}
```

### Message Protocol

#### Command Message (Client → Server)

Send a command to execute:

```json
{
  "type": "command",
  "command": "ls -la",
  "id": "unique_command_id",
  "timeout": 30
}
```

**Fields:**

- `type`: Must be "command"
- `command`: Shell command to execute (string)
- `id`: Unique identifier for tracking (string)
- `timeout`: Optional timeout in seconds (integer, default: 30)

#### Response Message (Server → Client)

Command execution result:

```json
{
  "type": "response",
  "id": "unique_command_id",
  "stdout": "command output...",
  "stderr": "error output...",
  "exit_code": 0,
  "execution_time": 0.123,
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

**Fields:**

- `type`: "response"
- `id`: Matches the command ID
- `stdout`: Standard output from command
- `stderr`: Standard error from command
- `exit_code`: Command exit code (0 = success)
- `execution_time`: Time taken in seconds
- `timestamp`: UTC timestamp of response

#### Error Message (Server → Client)

Error notification:

```json
{
  "type": "error",
  "message": "Error description",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

## Security

### Authentication

- All WebSocket connections require a valid device token
- Tokens are validated using constant-time comparison (prevents timing attacks)
- Invalid tokens result in connection rejection (HTTP 403)

### Command Security

The server implements several security measures:

1. **Command Blacklist**: Dangerous commands are blocked (e.g., `rm -rf /`)
2. **Timeout Protection**: Commands have maximum execution time (default: 30s)
3. **Length Validation**: Commands have maximum length (default: 1000 chars)
4. **Logging**: All command executions are logged for audit

**Blocked Commands:**

- `rm -rf /` - Recursive delete
- `:(){ :|:& };:` - Fork bomb
- `mkfs` - Format filesystem
- `dd if=/dev/zero` - Zero out devices
- `chmod -R 777 /` - Dangerous permission changes

### Recommendations for Production

1. **Use HTTPS/WSS**: Enable TLS for encrypted connections
2. **Strong Tokens**: Use cryptographically secure random tokens
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Firewall**: Restrict access to trusted networks
5. **Command Whitelist**: Consider implementing command whitelist instead of blacklist
6. **Monitoring**: Set up monitoring and alerting for suspicious activity

## Architecture

### Components

```
server/
├── __init__.py              # Package initialization
├── main.py                  # FastAPI application entry point
├── websocket_handler.py     # WebSocket connection manager
├── shell_executor.py        # Command execution engine
├── auth.py                  # Authentication logic
├── models.py                # Pydantic data models
├── config.py                # Configuration management
└── requirements.txt         # Python dependencies
```

### Flow Diagram

```
Client                    Server
  |                         |
  |--- Connect (token) ---->|
  |                         |--> Validate token
  |                         |--> Register device
  |<--- Accept connection --|
  |                         |
  |--- Command message ---->|
  |                         |--> Validate command
  |                         |--> Execute command
  |                         |--> Capture output
  |<--- Response message ---|
  |                         |
  |--- Disconnect ----------|
  |                         |--> Cleanup device
```

## Development

### Running Tests

Test the server with the included test scripts:

```bash
# Test basic functionality
python3 /tmp/test_websocket.py

# Test security features
python3 /tmp/test_security.py
```

### Debugging

Enable debug logging by setting `LOG_LEVEL=DEBUG` in `.env`:

```env
LOG_LEVEL=DEBUG
```

### Adding New Features

1. **New Command Validators**: Add to `shell_executor.py`
2. **New Message Types**: Add models to `models.py`
3. **New Endpoints**: Add to `main.py`
4. **New Authentication Methods**: Extend `auth.py`

## Troubleshooting

### Connection Refused

- Ensure server is running: `curl http://localhost:8000/health`
- Check firewall settings
- Verify correct port in configuration

### Authentication Failed

- Verify token is configured in `.env` file
- Check token format: `device_id:token`
- Ensure token matches exactly (case-sensitive)

### Command Not Executing

- Check command is not in blacklist
- Verify command timeout is sufficient
- Check server logs for error messages

### High CPU Usage

- Check for long-running commands
- Review command timeout settings
- Monitor connected devices

## License

MIT

## Support

For issues and questions, please create an issue in the repository.
