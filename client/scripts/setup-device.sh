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
