#!/bin/bash
#
# Device Setup Helper
# Helps configure a new device with server connection details
#

set -e

CONFIG_FILE="/etc/remoteshell/config.yaml"

echo "======================================"
echo "RemoteShell Device Setup"
echo "======================================"
echo

# Check if config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found at $CONFIG_FILE"
    echo "Please run install.sh first"
    exit 1
fi

# Get user input
read -p "Enter server hostname/IP: " SERVER_HOST
read -p "Enter server port [8000]: " SERVER_PORT
SERVER_PORT=${SERVER_PORT:-8000}

read -p "Enter device ID: " DEVICE_ID
read -sp "Enter device token: " DEVICE_TOKEN
echo

read -p "Use SSL/TLS? (y/n) [n]: " USE_SSL
USE_SSL=${USE_SSL:-n}

# Update config file
echo
echo "Updating configuration..."

# Create temporary file with updates
cat > /tmp/config.yaml.tmp << EOF
server:
  host: "$SERVER_HOST"
  port: $SERVER_PORT
  use_ssl: $([ "$USE_SSL" = "y" ] && echo "true" || echo "false")
  reconnect_interval: 5
  max_reconnect_attempts: 0
  ping_interval: 30
  ping_timeout: 10

device:
  device_id: "$DEVICE_ID"
  token: "$DEVICE_TOKEN"

execution:
  timeout: 30
  shell: "/bin/bash"
  working_directory: "~"
  capture_output: true

logging:
  level: "INFO"
  file: "/var/log/remoteshell/client.log"
  console: true
  max_size: 10485760
  backup_count: 5

security:
  validate_ssl: true
  allowed_commands: []
  blocked_commands:
    - "rm -rf /"
    - "mkfs"
    - "dd if=/dev/zero"
EOF

# Backup existing config
cp "$CONFIG_FILE" "$CONFIG_FILE.backup"

# Move new config
mv /tmp/config.yaml.tmp "$CONFIG_FILE"
chmod 600 "$CONFIG_FILE"

# Set ownership if remoteshell user exists
if id remoteshell &>/dev/null; then
    chown remoteshell:remoteshell "$CONFIG_FILE"
else
    echo "Warning: remoteshell user not found. Please run install.sh first or manually set ownership."
fi

echo
echo "Configuration updated successfully!"
echo "Backup saved to: $CONFIG_FILE.backup"
echo
echo "To start the client:"
echo "  sudo systemctl start remoteshell-client"
echo
