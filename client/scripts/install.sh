#!/bin/bash
set -e

echo "===================================="
echo "RemoteShell Client Installation"
echo "===================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Note: Running as root. Will create remoteshell user."
    CREATE_USER=true
else
    echo "Running as non-root user: $(whoami)"
    CREATE_USER=false
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
cd "$(dirname "$0")/.."
pip3 install -r requirements.txt

# Create user if needed
if [ "$CREATE_USER" = true ]; then
    if ! id remoteshell &>/dev/null; then
        echo ""
        echo "Creating remoteshell user..."
        useradd -r -s /bin/bash -d /opt/remoteshell -m remoteshell
        echo "User remoteshell created"
    else
        echo "User remoteshell already exists"
    fi
fi

# Copy files to installation directory
if [ "$CREATE_USER" = true ]; then
    echo ""
    echo "Installing files to /opt/remoteshell..."
    mkdir -p /opt/remoteshell/client
    cp -r . /opt/remoteshell/client/
    chown -R remoteshell:remoteshell /opt/remoteshell
    echo "Files installed"
fi

echo ""
echo "===================================="
echo "Installation complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Run setup-device.sh to configure the client"
echo "2. Edit config.yaml with your server URL and token"
if [ "$CREATE_USER" = true ]; then
    echo "3. Install systemd service (optional):"
    echo "   sudo cp ../../systemd/remoteshell-client.service /etc/systemd/system/"
    echo "   sudo systemctl daemon-reload"
    echo "   sudo systemctl enable remoteshell-client"
    echo "   sudo systemctl start remoteshell-client"
fi
echo ""
