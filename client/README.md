# RemoteShell Client

Linux client for RemoteShell Manager system. Connects to the server via WebSocket and executes commands remotely.

## Features

- WebSocket connection with automatic reconnection
- Token-based authentication
- Secure command execution
- Configurable via YAML
- Comprehensive logging
- Command timeout and security controls

## Installation

### Prerequisites

- Python 3.9 or higher
- Linux operating system

### Install Dependencies

```bash
cd client
pip install -r requirements.txt
```

## Configuration

1. Copy the example configuration:
```bash
cp config.yaml.example config.yaml
```

2. Edit `config.yaml` with your settings:
```yaml
server:
  host: "your-server.com"
  port: 8000

device:
  device_id: "my-device"
  token: "your-device-token"
```

## Usage

### Run Client

```bash
python main.py
```

### Run with Custom Config

```bash
python main.py --config /path/to/config.yaml
```

### Run as Background Service

```bash
nohup python main.py > /dev/null 2>&1 &
```

## Systemd Service

Create `/etc/systemd/system/remoteshell-client.service`:

```ini
[Unit]
Description=RemoteShell Client
After=network.target

[Service]
Type=simple
User=remoteshell
WorkingDirectory=/opt/remoteshell/client
ExecStart=/usr/bin/python3 /opt/remoteshell/client/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable remoteshell-client
sudo systemctl start remoteshell-client
sudo systemctl status remoteshell-client
```

## Security

- Store tokens securely
- Use SSL/TLS in production
- Restrict file permissions: `chmod 600 config.yaml`
- Configure command blacklist/whitelist
- Run with minimal privileges

## Logging

Logs are written to:
- Console (if enabled)
- `client.log` file (configurable)

View logs:
```bash
tail -f client.log
```

## Troubleshooting

### Connection Issues

- Check network connectivity
- Verify server URL and port
- Check token validity
- Review logs for errors

### Command Execution Issues

- Check shell configuration
- Verify working directory exists
- Review security settings
- Check command timeout values

## License

MIT
