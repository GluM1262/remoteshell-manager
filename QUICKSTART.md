# Quick Start Guide

## RemoteShell Manager - Web Interface

Get started with the RemoteShell Manager web interface in just a few minutes!

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server:**
   ```bash
   python server/main.py
   ```

3. **Open your browser:**
   ```
   http://localhost:8000
   ```

## Using the Interface

### 1. View Connected Devices
- The left panel shows all connected devices
- Green indicator = Online
- Gray indicator = Offline
- Queue size shows pending commands

### 2. Send Commands
1. Select a target device from the dropdown
2. Enter your shell command (e.g., `ls -la`, `whoami`, `df -h`)
3. Set timeout (optional, default 30 seconds)
4. Click "Send Command"

### 3. View Results
- Results appear below the command panel
- Shows command, device, status, exit code
- Displays stdout and stderr
- Execution time is tracked

### 4. Browse History
- All commands are logged in the history section
- Filter by device or status
- Click any history item to view full results

## Demo Data

The server starts with 3 demo devices:
- `device1` - Online
- `device2` - Offline (2 queued commands)
- `device3` - Online

Commands are simulated with realistic outputs.

## API Documentation

Access interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

**Server won't start?**
- Check if port 8000 is already in use
- Verify Python version (3.9+)
- Ensure all dependencies are installed

**Can't connect to WebSocket?**
- Check browser console for errors
- Verify server is running
- Check firewall settings

**Commands not working?**
- Ensure device is online
- Check command syntax
- Review server logs for errors

## Next Steps

- Integrate with real device clients
- Add authentication
- Customize device types
- Extend command capabilities

Enjoy managing your remote devices! 🚀
