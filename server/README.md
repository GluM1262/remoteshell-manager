# RemoteShell Manager - Server

Web-based interface for managing remote Linux devices and executing commands.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the Server

```bash
# Start the server
python server/main.py
```

Or with uvicorn directly:

```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

## Access the Interface

Once the server is running, open your browser and navigate to:

```
http://localhost:8000
```

## API Documentation

Interactive API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Features

- 🖥️ Device management and monitoring
- ⚡ Real-time device status updates via WebSocket
- 📝 Command execution with live results
- 📊 Command history with filtering
- 🎨 Modern, responsive web interface
- 📱 Mobile-friendly design

## API Endpoints

- `GET /` - Web interface
- `GET /api/devices` - List all devices
- `GET /api/devices/{device_id}` - Get device details
- `POST /api/command` - Send command to device
- `GET /api/command/{command_id}` - Get command status
- `GET /api/history` - Get command history
- `GET /api/statistics` - Get system statistics
- `WS /ws` - WebSocket for real-time updates

## Directory Structure

```
server/
├── main.py              # FastAPI application
├── static/              # Static files
│   ├── index.html       # Main HTML page
│   ├── css/
│   │   └── style.css    # Styles
│   └── js/
│       ├── app.js       # Main application logic
│       ├── api.js       # API client
│       └── websocket.js # WebSocket client
└── templates/           # Optional Jinja2 templates
```
## Quick Start

```bash
# Start the server
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at `http://localhost:8000`

API documentation at `http://localhost:8000/docs`

## Configuration

Create a `.env` file in the server directory:

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key-here
TOKEN_EXPIRATION=3600

# Database
DATABASE_PATH=remoteshell.db
DATABASE_POOL_SIZE=5
HISTORY_RETENTION_DAYS=30

# Queue
MAX_QUEUE_SIZE=100
QUEUE_TIMEOUT=300
COMMAND_DEFAULT_TIMEOUT=30

# WebSocket
WEBSOCKET_TIMEOUT=60
WEBSOCKET_PING_INTERVAL=30

# CORS
CORS_ORIGINS=["*"]
```

## API Usage Examples

### Send Command to Device

```bash
curl -X POST "http://localhost:8000/api/command" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device1",
    "command": "ls -la /home",
    "timeout": 30
  }'

# Response:
{
  "command_id": "cmd_abc123",
  "status": "pending",
  "message": "Command queued successfully"
}
```

### Check Command Status

```bash
curl "http://localhost:8000/api/command/cmd_abc123"

# Response:
{
  "command_id": "cmd_abc123",
  "device_id": "device1",
  "command": "ls -la /home",
  "status": "completed",
  "created_at": "2026-02-08T10:00:00",
  "sent_at": "2026-02-08T10:00:01",
  "completed_at": "2026-02-08T10:00:02",
  "stdout": "total 48\ndrwxr-xr-x 5 user user 4096...",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.125
}
```

### List All Devices

```bash
curl "http://localhost:8000/api/devices"

# Response:
[
  {
    "device_id": "device1",
    "status": "online",
    "first_seen": "2026-02-08T09:00:00",
    "last_connected": "2026-02-08T10:00:00",
    "queue_size": 2,
    "total_commands": 15,
    "metadata": {"hostname": "server1", "ip": "192.168.1.100"}
  }
]
```

### Get Device History

```bash
curl "http://localhost:8000/api/devices/device1/history?limit=10"

# Response: Array of CommandStatus objects
```

### Get Device Statistics

```bash
curl "http://localhost:8000/api/devices/device1/statistics"

# Response:
{
  "total_commands": 100,
  "completed": 95,
  "failed": 3,
  "pending": 2,
  "timeout": 0,
  "avg_execution_time": 0.234
}
```

### Send Bulk Commands

```bash
curl -X POST "http://localhost:8000/api/commands/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": ["device1", "device2", "device3"],
    "command": "uptime",
    "timeout": 30
  }'

# Response: Array of CommandResponse objects
```

### Get Command History with Filters

```bash
# Get completed commands for a device
curl "http://localhost:8000/api/commands?device_id=device1&status=completed&limit=50"

# Get commands from date range
curl "http://localhost:8000/api/commands?start_date=2026-02-01T00:00:00&end_date=2026-02-08T23:59:59"
```

### Cancel Pending Command

```bash
curl -X DELETE "http://localhost:8000/api/command/cmd_abc123"

# Response:
{
  "message": "Command cancelled successfully"
}
```

### Cleanup Old Records

```bash
curl -X POST "http://localhost:8000/api/history/cleanup" \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'

# Response:
{
  "message": "Deleted 150 old records",
  "deleted_count": 150
}
```

### Export History

```bash
# Export as JSON
curl "http://localhost:8000/api/history/export?format=json&device_id=device1&limit=100"

# Export as CSV
curl "http://localhost:8000/api/history/export?format=csv&limit=1000" > history.csv
```

## WebSocket Protocol

### Device Connection

```
ws://localhost:8000/ws/{device_id}?token={device_token}
```

### Message Format

**Server → Device (Command)**
```json
{
  "type": "command",
  "command_id": "cmd_abc123",
  "command": "ls -la",
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

**Device → Server (Result)**
```json
{
  "type": "result",
  "command_id": "cmd_abc123",
  "stdout": "...",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.125
}
```

**Device → Server (Error)**
```json
{
  "type": "error",
  "command_id": "cmd_abc123",
  "error": "Command not found"
}
```

**Ping/Pong (Keep-alive)**
```json
// Device → Server
{"type": "ping"}

// Server → Device
{"type": "pong"}
```

## Database Schema

The server uses SQLite with the following tables:

### Devices Table
- `device_id` (TEXT, UNIQUE): Device identifier
- `device_token` (TEXT): Authentication token
- `first_seen` (TIMESTAMP): First connection time
- `last_connected` (TIMESTAMP): Last connection time
- `status` (TEXT): online/offline
- `metadata` (TEXT): JSON metadata

### Commands Table
- `command_id` (TEXT, UNIQUE): Command identifier
- `device_id` (TEXT): Target device
- `command` (TEXT): Command to execute
- `status` (TEXT): pending/sent/executing/completed/failed/timeout
- `created_at` (TIMESTAMP): Creation time
- `sent_at` (TIMESTAMP): Sent time
- `completed_at` (TIMESTAMP): Completion time
- `stdout` (TEXT): Command output
- `stderr` (TEXT): Error output
- `exit_code` (INTEGER): Exit code
- `execution_time` (REAL): Execution time in seconds
- `error_message` (TEXT): Error description

## Architecture

```
┌─────────────┐
│   Client    │
│  (Web UI)   │
└──────┬──────┘
       │ REST API
       │
┌──────▼──────────────────────────────────┐
│         FastAPI Server                   │
│  ┌────────────┐  ┌──────────────┐       │
│  │   Main     │  │  WebSocket   │       │
│  │  (REST)    │  │   Handler    │       │
│  └────┬───────┘  └──────┬───────┘       │
│       │                 │                │
│  ┌────▼─────────────────▼──────┐        │
│  │    Queue Manager             │        │
│  │  (Command Orchestration)     │        │
│  └──────────┬───────────────────┘        │
│             │                             │
│  ┌──────────▼────────┐  ┌────────────┐  │
│  │     Database      │  │  History   │  │
│  │  (SQLite/async)   │  │  Manager   │  │
│  └───────────────────┘  └────────────┘  │
└──────────────────────────────────────────┘
             │
             │ WebSocket
             │
    ┌────────▼────────┐
    │     Device      │
    │    (Client)     │
    └─────────────────┘
```

## Development

### Run Tests
```bash
pytest
```

### Code Style
```bash
black server/
isort server/
```

### Type Checking
```bash
mypy server/
```

## License

MIT
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
