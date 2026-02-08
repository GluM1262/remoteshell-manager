# RemoteShell Client Systemd Service Documentation

Comprehensive guide to the RemoteShell client systemd service configuration, management, and customization.

## Table of Contents

1. [Service Overview](#service-overview)
2. [Service File Configuration](#service-file-configuration)
3. [Environment Variables](#environment-variables)
4. [Security Features](#security-features)
5. [Service Management](#service-management)
6. [Customization](#customization)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Troubleshooting](#troubleshooting)

## Service Overview

The RemoteShell client runs as a systemd service (`remoteshell-client.service`) that:

- Starts automatically on boot
- Runs as a dedicated non-privileged user (`remoteshell`)
- Automatically restarts on failure
- Implements security hardening measures
- Integrates with systemd journal for logging

### Service Location

The service file is installed at:
```
/etc/systemd/system/remoteshell-client.service
```

## Service File Configuration

### Unit Section

```ini
[Unit]
Description=RemoteShell Client Agent
Documentation=https://github.com/GluM1262/remoteshell-manager
After=network-online.target
Wants=network-online.target
```

**Key directives:**
- `After`: Ensures network is available before starting
- `Wants`: Soft dependency on network (won't fail if network target fails)
- `Documentation`: Link to project documentation

### Service Section

```ini
[Service]
Type=simple
User=remoteshell
Group=remoteshell
WorkingDirectory=/opt/remoteshell/client
EnvironmentFile=-/etc/remoteshell/client.env
ExecStart=/usr/bin/python3 /opt/remoteshell/client/main.py --config /etc/remoteshell/config.yaml
```

**Key directives:**
- `Type=simple`: Main process doesn't fork
- `User/Group`: Runs with restricted privileges
- `WorkingDirectory`: Sets process working directory
- `EnvironmentFile`: Optional environment variables file (- prefix means don't fail if missing)
- `ExecStart`: Command to start the service

### Restart Policy

```ini
Restart=always
RestartSec=10
StartLimitInterval=5min
StartLimitBurst=3
```

**Behavior:**
- Restarts automatically on any exit (success or failure)
- Waits 10 seconds between restart attempts
- Maximum 3 restarts within 5 minutes before giving up
- Prevents restart loops

### Install Section

```ini
[Install]
WantedBy=multi-user.target
```

**Purpose:**
- Specifies when service should start
- `multi-user.target`: Normal multi-user system startup

## Environment Variables

Environment variables can be set in `/etc/remoteshell/client.env`:

```bash
# Python path (if using virtual environment)
PYTHONPATH=/opt/remoteshell/venv/lib/python3.9/site-packages

# Logging level
LOG_LEVEL=INFO

# Custom config path
CONFIG_PATH=/etc/remoteshell/config.yaml

# Python optimization
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### Using Virtual Environment

If using a Python virtual environment:

```bash
# Option 1: Set PYTHONPATH
PYTHONPATH=/opt/remoteshell/venv/lib/python3.9/site-packages

# Option 2: Modify ExecStart to use venv python
ExecStart=/opt/remoteshell/venv/bin/python3 /opt/remoteshell/client/main.py --config /etc/remoteshell/config.yaml
```

## Security Features

The service implements multiple security hardening measures:

### Privilege Restrictions

```ini
NoNewPrivileges=true
User=remoteshell
Group=remoteshell
```

- Prevents privilege escalation
- Runs as dedicated unprivileged user

### File System Protection

```ini
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/remoteshell /etc/remoteshell
PrivateTmp=true
```

- `ProtectSystem=strict`: Makes `/usr`, `/boot`, `/efi` read-only
- `ProtectHome=true`: Makes `/home`, `/root`, `/run/user` inaccessible
- `ReadWritePaths`: Explicitly allows writing to specific directories
- `PrivateTmp=true`: Service gets private `/tmp` and `/var/tmp`

### Kernel Protection

```ini
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
```

- Prevents modification of kernel parameters
- Prevents loading/unloading kernel modules
- Protects cgroup hierarchy

### System Call Restrictions

```ini
RestrictRealtime=true
RestrictNamespaces=true
LockPersonality=true
MemoryDenyWriteExecute=false
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
```

- `RestrictRealtime`: Prevents real-time scheduling
- `RestrictNamespaces`: Restricts namespace creation
- `LockPersonality`: Prevents changing execution domain
- `MemoryDenyWriteExecute=false`: Allows memory mapping (required for Python)
- `RestrictAddressFamilies`: Only allows IPv4, IPv6, and Unix sockets

### Resource Limits

```ini
LimitNOFILE=65536
LimitNPROC=512
```

- `LimitNOFILE`: Maximum 65,536 open files
- `LimitNPROC`: Maximum 512 processes

## Service Management

### Basic Commands

```bash
# Start service
sudo systemctl start remoteshell-client

# Stop service
sudo systemctl stop remoteshell-client

# Restart service
sudo systemctl restart remoteshell-client

# Reload configuration (if supported)
sudo systemctl reload remoteshell-client

# Check status
sudo systemctl status remoteshell-client

# Enable auto-start on boot
sudo systemctl enable remoteshell-client

# Disable auto-start
sudo systemctl disable remoteshell-client
```

### Service Status

Check detailed service status:

```bash
sudo systemctl status remoteshell-client -l --no-pager
```

Output includes:
- Current state (active, inactive, failed)
- Process ID
- Memory usage
- Recent log entries
- Uptime

### Reload Systemd

After modifying the service file:

```bash
sudo systemctl daemon-reload
sudo systemctl restart remoteshell-client
```

## Customization

### Modifying Service File

1. Edit the service file:
```bash
sudo systemctl edit --full remoteshell-client
```

2. Make changes
3. Save and reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart remoteshell-client
```

### Override Configuration

Create an override file without modifying the main service file:

```bash
sudo systemctl edit remoteshell-client
```

Add overrides:
```ini
[Service]
Environment="LOG_LEVEL=DEBUG"
RestartSec=5
```

This creates: `/etc/systemd/system/remoteshell-client.service.d/override.conf`

### Common Customizations

#### Change Restart Delay

```ini
[Service]
RestartSec=5
```

#### Add Pre-Start Script

```ini
[Service]
ExecStartPre=/usr/local/bin/pre-start-checks.sh
```

#### Change User

```ini
[Service]
User=myuser
Group=mygroup
```

#### Add Environment Variables

```ini
[Service]
Environment="DEBUG=1"
Environment="CUSTOM_VAR=value"
```

#### Adjust Resource Limits

```ini
[Service]
LimitNOFILE=100000
LimitNPROC=1024
MemoryMax=512M
CPUQuota=50%
```

## Monitoring and Logging

### Journal Logs

View logs using journalctl:

```bash
# Follow logs in real-time
sudo journalctl -u remoteshell-client -f

# Last 100 lines
sudo journalctl -u remoteshell-client -n 100

# Logs since specific time
sudo journalctl -u remoteshell-client --since "2024-01-01 00:00:00"
sudo journalctl -u remoteshell-client --since "1 hour ago"
sudo journalctl -u remoteshell-client --since today

# Logs with specific priority
sudo journalctl -u remoteshell-client -p err
sudo journalctl -u remoteshell-client -p warning

# Export logs
sudo journalctl -u remoteshell-client -o json-pretty > /tmp/logs.json
```

### Service Monitoring

Monitor service health:

```bash
# Check if service is active
systemctl is-active remoteshell-client

# Check if service is enabled
systemctl is-enabled remoteshell-client

# Show service properties
systemctl show remoteshell-client

# Show specific properties
systemctl show remoteshell-client -p MainPID,ActiveState,SubState
```

### Resource Usage

Monitor resource consumption:

```bash
# Real-time resource usage
systemd-cgtop

# Service-specific resource usage
systemctl status remoteshell-client | grep -E "Memory|CPU"

# Detailed resource accounting
systemd-cgtop -1 | grep remoteshell
```

## Troubleshooting

### Service Won't Start

**Check status and errors:**
```bash
sudo systemctl status remoteshell-client -l
sudo journalctl -u remoteshell-client -n 50 --no-pager
```

**Common issues:**

1. **Permission denied:**
   ```bash
   sudo chown -R remoteshell:remoteshell /opt/remoteshell
   sudo chown -R remoteshell:remoteshell /etc/remoteshell
   sudo chmod 600 /etc/remoteshell/config.yaml
   ```

2. **Python not found:**
   ```bash
   which python3
   # Update ExecStart path if needed
   ```

3. **Config file error:**
   ```bash
   sudo -u remoteshell python3 /opt/remoteshell/client/main.py --config /etc/remoteshell/config.yaml
   ```

### Service Keeps Restarting

**Check restart limits:**
```bash
sudo journalctl -u remoteshell-client | grep -i "start limit"
```

**If hitting start limit:**
```bash
# Reset failed state
sudo systemctl reset-failed remoteshell-client

# Restart service
sudo systemctl restart remoteshell-client
```

**Adjust restart limits:**
```bash
sudo systemctl edit remoteshell-client
```

Add:
```ini
[Service]
StartLimitIntervalSec=10min
StartLimitBurst=5
```

### High CPU/Memory Usage

**Monitor resources:**
```bash
top -p $(systemctl show -p MainPID remoteshell-client | cut -d= -f2)
```

**Set resource limits:**
```bash
sudo systemctl edit remoteshell-client
```

Add:
```ini
[Service]
MemoryMax=512M
MemoryHigh=384M
CPUQuota=50%
```

### Network Connection Issues

**Check network target:**
```bash
systemctl status network-online.target
```

**Add delay before start:**
```bash
sudo systemctl edit remoteshell-client
```

Add:
```ini
[Service]
ExecStartPre=/bin/sleep 10
```

### Debugging Service Execution

**Run service command manually:**
```bash
sudo -u remoteshell /usr/bin/python3 /opt/remoteshell/client/main.py --config /etc/remoteshell/config.yaml
```

**Enable debug logging:**
```bash
sudo systemctl edit remoteshell-client
```

Add:
```ini
[Service]
Environment="LOG_LEVEL=DEBUG"
```

**Check file permissions:**
```bash
sudo -u remoteshell ls -la /opt/remoteshell/client
sudo -u remoteshell cat /etc/remoteshell/config.yaml
```

## Best Practices

1. **Always reload systemd after changes:**
   ```bash
   sudo systemctl daemon-reload
   ```

2. **Test changes before enabling:**
   ```bash
   sudo systemctl start remoteshell-client
   # Verify it works
   sudo systemctl enable remoteshell-client
   ```

3. **Keep service file simple:**
   - Use overrides for customizations
   - Store environment variables in separate file

4. **Monitor logs regularly:**
   ```bash
   sudo journalctl -u remoteshell-client --since "1 day ago" | grep -i error
   ```

5. **Use appropriate restart policies:**
   - Development: `Restart=on-failure`
   - Production: `Restart=always`

6. **Document customizations:**
   - Keep comments in override files
   - Maintain changelog of modifications

## References

- [systemd.service man page](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [systemd.exec man page](https://www.freedesktop.org/software/systemd/man/systemd.exec.html)
- [systemd.unit man page](https://www.freedesktop.org/software/systemd/man/systemd.unit.html)
- [journalctl man page](https://www.freedesktop.org/software/systemd/man/journalctl.html)

## Support

For issues specific to the RemoteShell client service:
- GitHub Issues: https://github.com/GluM1262/remoteshell-manager/issues
- Documentation: https://github.com/GluM1262/remoteshell-manager

For systemd-specific questions:
- systemd GitHub: https://github.com/systemd/systemd
- systemd mailing list: systemd-devel@lists.freedesktop.org
