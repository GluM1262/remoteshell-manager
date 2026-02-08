# RemoteShell Manager

Remote Linux device management system via WebSocket.

## Description

RemoteShell Manager is a client-server application for remote execution of commands on Linux devices in real-time mode.

## Technology Stack

- Python 3.9+
- FastAPI
- WebSocket
- asyncio

## Project Structure

```
remoteshell-manager/
├── server/                 # FastAPI server application
│   ├── __init__.py
│   ├── main.py            # FastAPI entry point
│   ├── websocket_handler.py
│   ├── shell_executor.py
│   ├── auth.py
│   ├── models.py
│   ├── config.py
│   ├── requirements.txt
│   └── README.md          # Detailed server documentation
├── .env.example           # Example environment configuration
├── .gitignore
└── README.md
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

See [server/README.md](server/README.md) for complete installation and configuration instructions.

## License

MIT