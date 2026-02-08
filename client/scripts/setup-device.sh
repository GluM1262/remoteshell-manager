#!/bin/bash
set -e

echo "===================================="
echo "RemoteShell Client Configuration"
echo "===================================="
echo ""

# Get configuration directory
CONFIG_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_FILE="$CONFIG_DIR/config.yaml"

# Check if config already exists
if [ -f "$CONFIG_FILE" ]; then
    echo "Configuration file already exists: $CONFIG_FILE"
    read -p "Overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled"
        exit 0
    fi
fi

# Prompt for server URL
echo ""
read -p "Enter server URL (e.g., ws://server:8000/ws or wss://server:8000/ws): " SERVER_URL

# Prompt for token
echo ""
read -p "Enter device authentication token: " TOKEN

# Prompt for SSL validation
echo ""
read -p "Validate SSL certificates? (Y/n): " VALIDATE_SSL
VALIDATE_SSL=${VALIDATE_SSL:-Y}
if [[ $VALIDATE_SSL =~ ^[Yy]$ ]]; then
    VALIDATE_SSL_VAL="true"
else
    VALIDATE_SSL_VAL="false"
fi

# Prompt for whitelist
echo ""
read -p "Enable command whitelist? (y/N): " ENABLE_WHITELIST
if [[ $ENABLE_WHITELIST =~ ^[Yy]$ ]]; then
    WHITELIST_VAL="true"
else
    WHITELIST_VAL="false"
fi

# Determine use_ssl from URL
if [[ $SERVER_URL == wss://* ]]; then
    USE_SSL="true"
else
    USE_SSL="false"
fi

# Create configuration file
cat > "$CONFIG_FILE" << EOFCONFIG
# RemoteShell Client Configuration

server:
  url: "${SERVER_URL}"
  token: "${TOKEN}"
  use_ssl: ${USE_SSL}
  reconnect_interval: 10
  ping_interval: 30

security:
  validate_ssl: ${VALIDATE_SSL_VAL}
  enable_whitelist: ${WHITELIST_VAL}
  allowed_commands:
    - "ls"
    - "pwd"
    - "whoami"
    - "hostname"
    - "uptime"
    - "df"
    - "free"
    - "ps"
  blocked_commands: []
  max_execution_time: 30
  max_command_length: 1000
  allow_shell_operators: false

logging:
  level: "INFO"
  file: "client.log"
  max_size: 10485760  # 10MB
  backup_count: 5
EOFCONFIG

# Set permissions
chmod 600 "$CONFIG_FILE"

echo ""
echo "===================================="
echo "Configuration created: $CONFIG_FILE"
echo "===================================="
echo ""
echo "You can now run the client with:"
echo "  cd $CONFIG_DIR"
echo "  python3 main.py"
echo ""
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
