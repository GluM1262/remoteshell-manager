# RemoteShell Manager Server

FastAPI server for remote Linux device management via WebSocket.

## Features

- **Command Queue System**: Queue commands for devices, even when offline
- **Device Management**: Track device status, connection history
- **SQLite History Storage**: Persistent storage of commands and results
- **WebSocket Communication**: Real-time command execution
- **REST API**: Complete API for device and command management
- **Statistics & Analytics**: Command execution statistics
- **History Export**: Export history to JSON or CSV

## Installation

```bash
cd server
pip install -r requirements.txt
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
