# Security Guide

Security features and best practices for RemoteShell Manager.

## Core Security Features

### 1. Non-Root Execution

**Agent runs as unprivileged user:**

```bash
# Create dedicated user
sudo useradd -r -s /bin/bash -d /opt/remoteshell remoteshell

# Install agent as this user
sudo -u remoteshell python -m pip install -r requirements.txt

# Run via systemd with User directive
sudo systemctl edit remoteshell-client.service
```

Add to service file:
```ini
[Service]
User=remoteshell
Group=remoteshell
```

**Verify:**
```bash
ps aux | grep remoteshell
# Should NOT show root user
```

### 2. Command Whitelist

**Enable strict whitelist mode:**

Server (`server/.env`):
```bash
ENABLE_COMMAND_WHITELIST=true
ALLOWED_COMMANDS=ls,pwd,whoami,hostname,uptime,df,free,ps
```

Client (`client/config.yaml`):
```yaml
security:
  enable_whitelist: true
  allowed_commands:
    - "ls"
    - "pwd"
    - "whoami"
    - "hostname"
```

**Behavior:**
- ✅ Only whitelisted commands execute
- ❌ All other commands blocked
- 📝 Blocked attempts logged

### 3. Maximum Execution Time

**Enforce timeout limits:**

Server:
```bash
MAX_EXECUTION_TIME=30
```

Client:
```yaml
security:
  max_execution_time: 30
```

**Behavior:**
- Commands killed after timeout
- Prevents hanging processes
- Protects against resource exhaustion

### 4. TLS Encryption

**Enable encrypted communication:**

Server:
```bash
USE_TLS=true
TLS_CERT_PATH=tls/cert.pem
TLS_KEY_PATH=tls/key.pem
```

Client:
```yaml
server:
  url: "wss://your-server.com:8000/ws"
  use_ssl: true
security:
  validate_ssl: true
```

**Generate certificates:**
```bash
cd server/tls
./generate_certs.sh
```

## Security Best Practices

### Minimal Permissions

1. **Run as dedicated user:**
```bash
sudo useradd -r -s /bin/bash remoteshell
sudo usermod -L remoteshell  # Lock password
```

2. **Restrict file permissions:**
```bash
chmod 600 client/config.yaml
chmod 600 server/.env
chmod 600 server/tls/key.pem
```

3. **Limit systemd capabilities:**
```ini
[Service]
User=remoteshell
Group=remoteshell
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/remoteshell
```

### Command Security

1. **Use whitelist in production:**
```bash
ENABLE_COMMAND_WHITELIST=true
```

2. **Block dangerous commands:**
```yaml
security:
  blocked_commands:
    - "rm -rf /"
    - "mkfs"
    - "dd if=/dev/zero"
```

3. **Disable shell operators:**
```yaml
security:
  allow_shell_operators: false
```

### Network Security

1. **Always use TLS in production:**
```bash
USE_TLS=true
```

2. **Validate SSL certificates:**
```yaml
security:
  validate_ssl: true
```

3. **Firewall rules:**
```bash
# Only allow from specific IPs
sudo ufw allow from 10.0.0.0/8 to any port 8000
sudo ufw enable
```

### Token Security

1. **Use strong tokens:**
```bash
# Generate secure token
openssl rand -hex 32
```

2. **Rotate tokens regularly:**
```bash
# Update every 90 days
*/
```

3. **Secure token storage:**
```bash
chmod 600 config.yaml
```

## Security Checklist

- [ ] Agent runs as non-root user
- [ ] Command whitelist enabled (production)
- [ ] Execution timeout configured
- [ ] TLS encryption enabled
- [ ] SSL certificate validation enabled
- [ ] Config file permissions set to 600
- [ ] Strong device tokens (32+ characters)
- [ ] Firewall rules configured
- [ ] Dangerous commands blocked
- [ ] Shell operators disabled
- [ ] systemd security hardening enabled
- [ ] Logs monitored regularly

## Threat Model

### Protected Against:

✅ Unauthorized command execution  
✅ Privilege escalation  
✅ Resource exhaustion (timeout)  
✅ Network eavesdropping (TLS)  
✅ Dangerous commands (blacklist)  
✅ Token theft (secure storage)

### Not Protected Against:

❌ Compromised server (trusted server assumed)  
❌ Malicious whitelisted commands  
❌ Physical access to client machine  
❌ Kernel exploits

## Incident Response

### Suspicious Activity

1. **Check logs:**
```bash
sudo journalctl -u remoteshell-client -n 100
grep "Blocked command" /var/log/remoteshell/*.log
```

2. **Review command history:**
```bash
grep "Command executed" /var/log/remoteshell/*.log | tail -50
```

3. **Rotate tokens:**
```bash
# Generate new token
NEW_TOKEN=$(openssl rand -hex 32)
# Update config and restart
```

### Compromise Response

1. **Stop service immediately:**
```bash
sudo systemctl stop remoteshell-client
sudo systemctl stop remoteshell-server
```

2. **Revoke device token on server**

3. **Review all executed commands**

4. **Investigate and patch vulnerability**

5. **Rotate all tokens**

## Compliance

### Audit Logging

All command executions logged:
- Command text
- Device ID
- Timestamp
- Result (success/failure)
- stdout/stderr

### Data Retention

Configure retention policy:
```ini
[Service]
# Rotate logs weekly
LogsDirectory=remoteshell
LogsDirectoryMode=0750
```

## References

- OWASP Top 10
- CIS Benchmarks for Linux
- systemd Security Guidelines
- TLS Best Practices (Mozilla SSL Configuration Generator)

## Support

Security issues: security@your-domain.com

## Additional Security Measures

### Rate Limiting

Consider implementing rate limiting to prevent abuse:
- Maximum commands per minute
- Maximum connection attempts
- Cooldown periods after failures

### Command Logging

Log all commands with context:
```python
logger.info(f"Command: {command}, User: {device_id}, Time: {timestamp}")
```

### Intrusion Detection

Monitor for suspicious patterns:
- Repeated blocked commands
- Connection attempts from unusual locations
- Commands executed outside normal hours

### Network Segmentation

Isolate RemoteShell network:
- Dedicated VLAN for managed devices
- Separate server network
- No direct internet access for clients

### Principle of Least Privilege

Only grant necessary permissions:
- Minimal command whitelist
- Read-only access where possible
- No sudo/root commands

### Defense in Depth

Multiple security layers:
1. Network (firewall, VPN)
2. Transport (TLS encryption)
3. Application (whitelist, timeout)
4. System (non-root user, capabilities)
5. Audit (logging, monitoring)
