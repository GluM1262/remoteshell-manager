# RemoteShell Manager - Examples

This directory contains example configurations and scripts to help you get started with RemoteShell Manager.

## Files

### Configuration Examples

- **server_config.env** - Example server configuration with all available options
- **client_config.yaml** - Example client configuration with security settings

### Scripts

- **quickstart.sh** - Complete automated setup for testing
- **test_commands.sh** - Test script to send commands via API

## Quick Start

### 1. Automated Setup

Run the quickstart script for a complete test environment:

```bash
cd examples
./quickstart.sh
```

This will:
- Install Python dependencies
- Generate a test authentication token
- Configure server and client
- Provide instructions to start both components

### 2. Manual Setup

#### Server Setup

```bash
# Copy example configuration
cd server
cp ../examples/server_config.env .env

# Edit configuration
nano .env

# Generate authentication token
TOKEN=$(openssl rand -hex 16)
echo "DEVICE_TOKENS=$TOKEN" >> .env

# Start server
python3 main.py
```

#### Client Setup

```bash
# Copy example configuration
cd client
cp ../examples/client_config.yaml config.yaml

# Edit configuration (add your token and server URL)
nano config.yaml

# Start client
python3 main.py
```

### 3. Web Interface

Once the server is running, open your browser to:

```
http://localhost:8000/web
```

Or access the API documentation at:

```
http://localhost:8000/docs
```

## Testing Commands

After both server and client are running:

```bash
# Get list of connected devices
curl http://localhost:8000/api/devices

# Send a command (replace DEVICE_ID with actual ID)
curl -X POST "http://localhost:8000/api/devices/DEVICE_ID/command?command=whoami"

# View command history
curl http://localhost:8000/api/history

# Use the test script
cd examples
./test_commands.sh device_abc123456789
```

## Security Best Practices

When moving to production:

1. **Generate Strong Tokens**: Use `openssl rand -hex 32` for production tokens
2. **Enable TLS**: Set `USE_TLS=true` and configure certificates
3. **Enable Whitelist**: Set `ENABLE_COMMAND_WHITELIST=true`
4. **Limit Commands**: Only allow necessary commands in whitelist
5. **Run as Non-Root**: Use systemd service with `remoteshell` user
6. **Firewall**: Restrict access to server port (8000)
7. **Monitor Logs**: Review logs regularly for security events

## Troubleshooting

### Server won't start

- Check Python version: `python3 --version` (requires 3.9+)
- Install dependencies: `pip3 install -r server/requirements.txt`
- Check port 8000 is available: `netstat -tuln | grep 8000`
- Review logs for errors

### Client can't connect

- Verify server is running: `curl http://localhost:8000/`
- Check token in both server .env and client config.yaml
- Verify URL in client config (ws:// for no TLS, wss:// for TLS)
- Check firewall/network connectivity

### Commands not executing

- Check client logs: `tail -f client/client.log`
- Verify command is allowed (check whitelist/blacklist)
- Check command timeout settings
- Review security manager logs on server

## Additional Resources

- Main README: `../README.md`
- Security Guide: `../docs/SECURITY.md`
- Setup Guide: `../SETUP.md`
- TLS Configuration: `../server/tls/README.md`
- SystemD Services: `../systemd/README.md`
