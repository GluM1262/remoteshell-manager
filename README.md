# RemoteShell Manager

Remote Linux device management system via WebSocket with a modern web interface.

## Description

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

## Project Structure

```
remoteshell-manager/
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

## License

MIT