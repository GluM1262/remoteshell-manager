# RemoteShell Manager - Usage Examples

This document provides practical examples for using the RemoteShell Manager system.

## Starting the Server

```bash
cd server
python main.py
```

Or with custom settings:

```bash
# Create .env file
cat > .env << EOF
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO
DATABASE_PATH=remoteshell.db
COMMAND_DEFAULT_TIMEOUT=30
EOF

python main.py
```

The server will start on `http://localhost:8000`

## Connecting a Device

### Using the Example Client

```bash
# Install dependencies (if not already installed)
pip install websockets

# Run the client
python example_client.py \
  --server ws://localhost:8000 \
  --device-id my_device_001 \
  --token my_secret_token
```

### Using Custom Client Code

```python
import asyncio
import json
import websockets

async def connect_device():
    device_id = "my_device_001"
    token = "my_secret_token"
    
    uri = f"ws://localhost:8000/ws/{device_id}?token={token}"
    
    async with websockets.connect(uri) as websocket:
        print("Connected to server")
        
        # Listen for commands
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "command":
                # Execute command here
                result = {
                    "type": "result",
                    "command_id": data["command_id"],
                    "stdout": "command output",
                    "stderr": "",
                    "exit_code": 0,
                    "execution_time": 0.1
                }
                await websocket.send(json.dumps(result))

asyncio.run(connect_device())
```

## Using the REST API

### 1. Send Command to Device

```bash
curl -X POST http://localhost:8000/api/command \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "my_device_001",
    "command": "ls -la /home",
    "timeout": 30,
    "priority": 0
  }'
```

Response:
```json
{
  "command_id": "cmd_abc123",
  "status": "pending",
  "message": "Command queued successfully"
}
```

### 2. Check Command Status

```bash
curl http://localhost:8000/api/command/cmd_abc123
```

Response:
```json
{
  "command_id": "cmd_abc123",
  "device_id": "my_device_001",
  "command": "ls -la /home",
  "status": "completed",
  "created_at": "2026-02-08T10:00:00",
  "sent_at": "2026-02-08T10:00:01",
  "completed_at": "2026-02-08T10:00:02",
  "stdout": "total 48\ndrwxr-xr-x...",
  "stderr": "",
  "exit_code": 0,
  "execution_time": 0.125,
  "error_message": null
}
```

### 3. List All Devices

```bash
curl http://localhost:8000/api/devices
```

### 4. Get Device Details

```bash
curl http://localhost:8000/api/devices/my_device_001
```

### 5. Get Device Command History

```bash
curl "http://localhost:8000/api/devices/my_device_001/history?limit=10"
```

### 6. Get Device Statistics

```bash
curl http://localhost:8000/api/devices/my_device_001/statistics
```

Response:
```json
{
  "total_commands": 100,
  "completed": 95,
  "failed": 3,
  "pending": 2,
  "timeout": 0,
  "avg_execution_time": 0.234
}
```

### 7. Send Bulk Commands

Send the same command to multiple devices:

```bash
curl -X POST http://localhost:8000/api/commands/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "device_ids": ["device1", "device2", "device3"],
    "command": "uptime",
    "timeout": 30,
    "priority": 0
  }'
```

### 8. Get Command History with Filters

```bash
# Get completed commands for a specific device
curl "http://localhost:8000/api/commands?device_id=my_device_001&status=completed&limit=50"

# Get commands from date range
curl "http://localhost:8000/api/commands?start_date=2026-02-01T00:00:00&end_date=2026-02-08T23:59:59"

# Get all pending commands
curl "http://localhost:8000/api/commands?status=pending"
```

### 9. Cancel Pending Command

```bash
curl -X DELETE http://localhost:8000/api/command/cmd_abc123
```

### 10. Export History

Export as JSON:
```bash
curl "http://localhost:8000/api/history/export?format=json&device_id=my_device_001&limit=100" > history.json
```

Export as CSV:
```bash
curl "http://localhost:8000/api/history/export?format=csv&limit=1000" > history.csv
```

### 11. Cleanup Old Records

Delete records older than 30 days:
```bash
curl -X POST http://localhost:8000/api/history/cleanup \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
```

### 12. Get Global Statistics

```bash
curl http://localhost:8000/api/statistics
```

## Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Send command
response = requests.post(
    f"{BASE_URL}/api/command",
    json={
        "device_id": "my_device_001",
        "command": "df -h",
        "timeout": 30
    }
)
command_id = response.json()["command_id"]

# Check status
import time
time.sleep(2)  # Wait for execution

response = requests.get(f"{BASE_URL}/api/command/{command_id}")
result = response.json()

print(f"Status: {result['status']}")
print(f"Output:\n{result['stdout']}")
print(f"Exit Code: {result['exit_code']}")
```

## Integration with Web Dashboard

```javascript
// JavaScript example for web dashboard

// Send command
async function sendCommand(deviceId, command) {
    const response = await fetch('http://localhost:8000/api/command', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            device_id: deviceId,
            command: command,
            timeout: 30
        })
    });
    
    const data = await response.json();
    return data.command_id;
}

// Check command status
async function getCommandStatus(commandId) {
    const response = await fetch(`http://localhost:8000/api/command/${commandId}`);
    return await response.json();
}

// List devices
async function listDevices() {
    const response = await fetch('http://localhost:8000/api/devices');
    return await response.json();
}

// Usage
const commandId = await sendCommand('device1', 'ls -la');
console.log('Command queued:', commandId);

// Poll for result
setInterval(async () => {
    const status = await getCommandStatus(commandId);
    if (status.status === 'completed') {
        console.log('Output:', status.stdout);
    }
}, 1000);
```

## Advanced Features

### Command Priority

Send high-priority commands that will be processed before normal commands:

```bash
curl -X POST http://localhost:8000/api/command \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "my_device_001",
    "command": "sudo reboot",
    "timeout": 30,
    "priority": 10
  }'
```

### Device Metadata

When a device connects, you can include metadata:

```python
# In your device client
metadata = {
    "hostname": "server1",
    "ip": "192.168.1.100",
    "os": "Ubuntu 22.04",
    "version": "1.0.0"
}

# This metadata is stored in the database and returned with device info
```

### Queue Management

Check device queue status:

```bash
curl http://localhost:8000/api/devices/my_device_001/queue
```

Response shows:
- Current queue size
- Pending commands
- Connection status

## Monitoring

### View API Documentation

OpenAPI/Swagger documentation is available at:
```
http://localhost:8000/docs
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Troubleshooting

### Device Cannot Connect

1. Check token is correct
2. Verify server is running: `curl http://localhost:8000/health`
3. Check WebSocket URL format: `ws://host:port/ws/{device_id}?token={token}`

### Command Stuck in Pending

1. Check if device is connected: `GET /api/devices/{device_id}`
2. Check queue status: `GET /api/devices/{device_id}/queue`
3. Verify device is processing messages from WebSocket

### Database Issues

View database directly:
```bash
sqlite3 remoteshell.db
sqlite> SELECT * FROM devices;
sqlite> SELECT * FROM commands ORDER BY created_at DESC LIMIT 10;
```

## Production Deployment

### Using Environment Variables

```bash
export HOST=0.0.0.0
export PORT=8000
export DATABASE_PATH=/var/lib/remoteshell/remoteshell.db
export LOG_LEVEL=INFO
export SECRET_KEY=$(openssl rand -hex 32)

python main.py
```

### Using Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t remoteshell-manager .
docker run -p 8000:8000 -v ./data:/app/data remoteshell-manager
```

### Behind Nginx

```nginx
server {
    listen 80;
    server_name remoteshell.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://localhost:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Security Best Practices

1. **Use Strong Tokens**: Generate random tokens for each device
2. **Enable HTTPS**: Use TLS/SSL in production
3. **Limit Command Scope**: Restrict what commands devices can execute
4. **Regular Cleanup**: Remove old command history periodically
5. **Monitor Access**: Log and monitor device connections
6. **Network Security**: Use firewall rules to restrict access

## Performance Tips

1. **Database Tuning**: For large deployments, consider PostgreSQL instead of SQLite
2. **Queue Limits**: Set appropriate `max_queue_size` to prevent memory issues
3. **History Cleanup**: Run regular cleanup to keep database size manageable
4. **Connection Pooling**: Use database connection pooling for better performance
5. **Load Balancing**: Deploy multiple server instances behind a load balancer

## License

MIT
