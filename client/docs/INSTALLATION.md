# RemoteShell Client Installation Guide

Complete guide for installing and configuring the RemoteShell client on Linux systems.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Configuration](#configuration)
4. [Service Management](#service-management)
5. [Troubleshooting](#troubleshooting)
6. [Security](#security)

## Prerequisites

### System Requirements

- Linux distribution (Ubuntu 20.04+, Debian 10+, CentOS 8+, or similar)
- Python 3.9 or higher
- systemd (for service management)
- Root or sudo access

### Check Python Version

```bash
python3 --version
```

If Python 3.9+ is not installed:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**CentOS/RHEL:**
```bash
sudo yum install python3 python3-pip
```

## Installation Methods

### Method 1: Automated Installation (Recommended)

1. Download the client:
```bash
git clone https://github.com/GluM1262/remoteshell-manager.git
cd remoteshell-manager/client
```

2. Run the installation script:
```bash
sudo ./scripts/install.sh
```

3. Configure the client:
```bash
sudo nano /etc/remoteshell/config.yaml
```

4. Start the service:
```bash
sudo systemctl start remoteshell-client
```

### Method 2: Manual Installation

1. Create directories:
```bash
sudo mkdir -p /opt/remoteshell/client
sudo mkdir -p /etc/remoteshell
sudo mkdir -p /var/log/remoteshell
```

2. Create service user:
```bash
sudo useradd --system --no-create-home --shell /bin/false remoteshell
```

3. Install dependencies:
```bash
pip3 install -r requirements.txt
```

4. Copy files:
```bash
sudo cp -r client/* /opt/remoteshell/client/
sudo cp client/config.yaml.example /etc/remoteshell/config.yaml
```

5. Install systemd service:
```bash
sudo cp client/systemd/remoteshell-client.service /etc/systemd/system/
sudo systemctl daemon-reload
```

6. Set permissions:
```bash
sudo chown -R remoteshell:remoteshell /opt/remoteshell
sudo chown -R remoteshell:remoteshell /etc/remoteshell
sudo chown -R remoteshell:remoteshell /var/log/remoteshell
sudo chmod 600 /etc/remoteshell/config.yaml
```

7. Enable service:
```bash
sudo systemctl enable remoteshell-client
```

## Configuration

### Basic Configuration

Edit `/etc/remoteshell/config.yaml`:

```yaml
server:
  host: "your-server.com"
  port: 8000
  use_ssl: true

device:
  device_id: "my-device"
  token: "your-secure-token-here"
```

### Quick Setup Helper

Use the setup script for interactive configuration:

```bash
sudo ./scripts/setup-device.sh
```

### Configuration Options

See `config.yaml.example` for all available options:

- **Server settings**: Connection, SSL, reconnection
- **Device settings**: ID and authentication token
- **Execution settings**: Timeout, shell, working directory
- **Logging settings**: Level, file rotation
- **Security settings**: Command filtering

## Service Management

### Start Service

```bash
sudo systemctl start remoteshell-client
```

### Stop Service

```bash
sudo systemctl stop remoteshell-client
```

### Restart Service

```bash
sudo systemctl restart remoteshell-client
```

### Check Status

```bash
sudo systemctl status remoteshell-client
```

### Enable Auto-start

```bash
sudo systemctl enable remoteshell-client
```

### View Logs

```bash
# Real-time logs
sudo journalctl -u remoteshell-client -f

# Last 100 lines
sudo journalctl -u remoteshell-client -n 100

# Today's logs
sudo journalctl -u remoteshell-client --since today

# Log file
sudo tail -f /var/log/remoteshell/client.log
```

## Troubleshooting

### Service Won't Start

1. Check service status:
```bash
sudo systemctl status remoteshell-client
```

2. Check logs:
```bash
sudo journalctl -u remoteshell-client -n 50
```

3. Verify configuration:
```bash
sudo python3 -c "import yaml; yaml.safe_load(open('/etc/remoteshell/config.yaml'))"
```

4. Check permissions:
```bash
ls -l /etc/remoteshell/config.yaml
ls -ld /var/log/remoteshell
```

### Connection Issues

1. Test network connectivity:
```bash
ping your-server.com
telnet your-server.com 8000
```

2. Verify token:
```bash
# Check if token is correct in config
sudo grep token /etc/remoteshell/config.yaml
```

3. Check firewall:
```bash
sudo iptables -L
sudo ufw status
```

### Command Execution Issues

1. Check shell configuration:
```bash
which bash
ls -l /bin/bash
```

2. Test command manually:
```bash
sudo -u remoteshell bash -c "ls -la"
```

3. Review security settings in config

## Security

### Best Practices

1. **Secure token storage:**
```bash
sudo chmod 600 /etc/remoteshell/config.yaml
```

2. **Use SSL/TLS in production:**
```yaml
server:
  use_ssl: true
```

3. **Configure command filtering:**
```yaml
security:
  blocked_commands:
    - "rm -rf /"
    - "mkfs"
    - "dd if=/dev/zero"
```

4. **Run with minimal privileges:**
   - Service runs as `remoteshell` user (not root)
   - Limited file system access
   - systemd security hardening enabled

5. **Regular updates:**
```bash
cd remoteshell-manager
git pull
sudo ./scripts/install.sh
sudo systemctl restart remoteshell-client
```

### Firewall Configuration

Allow outbound connections to server:

```bash
# UFW
sudo ufw allow out to your-server.com port 8000

# iptables
sudo iptables -A OUTPUT -p tcp -d your-server.com --dport 8000 -j ACCEPT
```

### SELinux Configuration

If using SELinux, you may need to configure policies:

```bash
# Allow network connections
sudo setsebool -P nis_enabled 1

# Or create custom policy if needed
sudo ausearch -m avc -ts recent | audit2allow -M remoteshell
sudo semodule -i remoteshell.pp
```

## Advanced Configuration

### Using a Virtual Environment

1. Create virtual environment:
```bash
sudo python3 -m venv /opt/remoteshell/venv
sudo /opt/remoteshell/venv/bin/pip install -r requirements.txt
```

2. Update service file to use venv:
```bash
sudo nano /etc/systemd/system/remoteshell-client.service
```

Change ExecStart to:
```ini
ExecStart=/opt/remoteshell/venv/bin/python3 /opt/remoteshell/client/main.py --config /etc/remoteshell/config.yaml
```

3. Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart remoteshell-client
```

### Log Rotation

The service logs to systemd journal by default. To configure log rotation:

```bash
sudo nano /etc/logrotate.d/remoteshell
```

Add:
```
/var/log/remoteshell/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 remoteshell remoteshell
    sharedscripts
    postrotate
        systemctl reload remoteshell-client > /dev/null 2>&1 || true
    endscript
}
```

### Running Multiple Clients

To run multiple client instances on the same machine:

1. Create separate config files:
```bash
sudo cp /etc/remoteshell/config.yaml /etc/remoteshell/config-device2.yaml
```

2. Create additional service files:
```bash
sudo cp /etc/systemd/system/remoteshell-client.service /etc/systemd/system/remoteshell-client@.service
```

3. Modify the service template to use instance name
4. Start instances:
```bash
sudo systemctl start remoteshell-client@device2
```

## Uninstallation

To completely remove the client:

```bash
cd remoteshell-manager/client
sudo ./scripts/uninstall.sh
```

To also remove configuration and logs:

```bash
sudo rm -rf /etc/remoteshell
sudo rm -rf /var/log/remoteshell
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/GluM1262/remoteshell-manager/issues
- Documentation: https://github.com/GluM1262/remoteshell-manager

## License

MIT License - See LICENSE file for details
