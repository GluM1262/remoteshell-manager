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
