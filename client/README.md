# RemoteShell Client

Production-ready Python client for executing remote commands on Linux devices via WebSocket.

## Features

- ✅ WebSocket connection with token authentication
- ✅ Automatic reconnection on connection loss
- ✅ Command execution with timeout enforcement
- ✅ Security validation (whitelist/blacklist)
- ✅ YAML-based configuration
- ✅ Rotating log files
- ✅ SSL/TLS support

## Installation

```bash
cd client
pip install -r requirements.txt
```

## Configuration

1. Copy example config:
```bash
cp config.yaml.example config.yaml
```

2. Edit `config.yaml` with your settings:
   - Server hostname/port
   - Device ID and token
   - Security settings

## Usage

```bash
python main.py --config config.yaml
```

## Configuration Reference

See `config.yaml.example` for all available options.

## Security

- Commands are validated against blacklist/whitelist
- Execution timeout is enforced
- SSL certificate validation (configurable)
- All operations are logged

## Logging

Logs are written to:
- Console (configurable)
- Rotating log file (default: `client.log`, 10MB max, 5 backups)

## Testing

After creating these files, test with:

```bash
cd client
python -m pytest tests/
```

## Requirements

- Python 3.9+
- websockets>=12.0
- pydantic>=2.0.0
- PyYAML>=6.0
