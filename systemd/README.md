# SystemD Service Installation Guide

This directory contains systemd service files for running RemoteShell Manager as system services with proper security hardening.

## Features

- ✅ Non-root execution (dedicated `remoteshell` user)
- ✅ Automatic restart on failure
- ✅ Security hardening (NoNewPrivileges, PrivateTmp, etc.)
- ✅ Capability restrictions
- ✅ Protected system directories

## Installation

### 1. Create Dedicated User

```bash
sudo useradd -r -s /bin/bash -d /opt/remoteshell remoteshell
sudo mkdir -p /opt/remoteshell
sudo chown remoteshell:remoteshell /opt/remoteshell
```

### 2. Install Application

```bash
# Copy application files
sudo cp -r server client /opt/remoteshell/
sudo chown -R remoteshell:remoteshell /opt/remoteshell

# Create virtual environment
sudo -u remoteshell python3 -m venv /opt/remoteshell/venv

# Install dependencies
sudo -u remoteshell /opt/remoteshell/venv/bin/pip install -r /opt/remoteshell/server/requirements.txt
sudo -u remoteshell /opt/remoteshell/venv/bin/pip install -r /opt/remoteshell/client/requirements.txt
```

### 3. Configure Application

```bash
# Server configuration
sudo -u remoteshell cp /opt/remoteshell/server/.env.example /opt/remoteshell/server/.env
sudo -u remoteshell nano /opt/remoteshell/server/.env

# Client configuration
sudo -u remoteshell cp /opt/remoteshell/client/config.yaml.example /opt/remoteshell/client/config.yaml
sudo -u remoteshell nano /opt/remoteshell/client/config.yaml

# Set proper permissions
sudo chmod 600 /opt/remoteshell/server/.env
sudo chmod 600 /opt/remoteshell/client/config.yaml
```

### 4. Install SystemD Services

```bash
# Copy service files
sudo cp systemd/remoteshell-server.service /etc/systemd/system/
sudo cp systemd/remoteshell-client.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable remoteshell-server.service
sudo systemctl enable remoteshell-client.service
```

### 5. Start Services

```bash
# Start server
sudo systemctl start remoteshell-server

# Start client
sudo systemctl start remoteshell-client

# Check status
sudo systemctl status remoteshell-server
sudo systemctl status remoteshell-client
```

## Service Management

### View Logs

```bash
# Server logs
sudo journalctl -u remoteshell-server -f

# Client logs
sudo journalctl -u remoteshell-client -f

# View last 100 lines
sudo journalctl -u remoteshell-server -n 100
```

### Restart Services

```bash
sudo systemctl restart remoteshell-server
sudo systemctl restart remoteshell-client
```

### Stop Services

```bash
sudo systemctl stop remoteshell-server
sudo systemctl stop remoteshell-client
```

### Disable Services

```bash
sudo systemctl disable remoteshell-server
sudo systemctl disable remoteshell-client
```

## Security Features

The service files include several security hardening measures:

### NoNewPrivileges
Prevents the service from gaining new privileges.

### PrivateTmp
Service gets a private /tmp directory.

### ProtectSystem=strict
Entire file system is read-only except specified paths.

### ProtectHome
Home directories are inaccessible.

### ReadWritePaths
Only /opt/remoteshell is writable.

### CapabilityBoundingSet
No capabilities are granted.

## Verification

### Verify User

Check that services run as `remoteshell` user:

```bash
ps aux | grep remoteshell
# Should show: remoteshell ... python main.py
```

### Verify Security

Check security status:

```bash
sudo systemd-analyze security remoteshell-server
sudo systemd-analyze security remoteshell-client
```

### Test Permissions

Try to access protected files (should fail):

```bash
sudo -u remoteshell cat /etc/shadow
# Should get: Permission denied
```

## Troubleshooting

### Service Won't Start

1. Check logs:
```bash
sudo journalctl -u remoteshell-server -n 50
```

2. Verify file permissions:
```bash
ls -la /opt/remoteshell/
```

3. Test manually:
```bash
sudo -u remoteshell /opt/remoteshell/venv/bin/python /opt/remoteshell/server/main.py
```

### Permission Denied Errors

Ensure files are owned by `remoteshell` user:
```bash
sudo chown -R remoteshell:remoteshell /opt/remoteshell
```

### Connection Issues

Check firewall:
```bash
sudo ufw status
sudo ufw allow 8000/tcp
```

## Additional Security

### AppArmor Profile

For additional security, consider creating an AppArmor profile:

```bash
sudo aa-genprof /opt/remoteshell/venv/bin/python
```

### Firewall Rules

Restrict access to specific IPs:

```bash
sudo ufw allow from 10.0.0.0/8 to any port 8000
```

## References

- systemd.service(5) manual
- systemd.exec(5) manual (security options)
- systemd-analyze(1) security analysis
