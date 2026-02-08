#!/bin/bash
# RemoteShell Manager - Quick Start Script

set -e

echo "========================================"
echo "RemoteShell Manager - Quick Start"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Python version: $(python3 --version)"
echo ""

# Install dependencies
echo "Installing dependencies..."
cd "$(dirname "$0")/.."
pip3 install -q -r server/requirements.txt -r client/requirements.txt
echo "✓ Dependencies installed"
echo ""

# Generate test token
TOKEN="test_$(openssl rand -hex 16)"
echo "Generated test token: $TOKEN"
echo ""

# Setup server
echo "Setting up server..."
cd server
cp .env.example .env
echo "DEVICE_TOKENS=$TOKEN" >> .env
echo "✓ Server configured"
echo ""

# Setup client  
echo "Setting up client..."
cd ../client
cp config.yaml.example config.yaml
sed -i "s/your-device-token-here/$TOKEN/" config.yaml 2>/dev/null || \
    sed -i '' "s/your-device-token-here/$TOKEN/" config.yaml 2>/dev/null || true
echo "✓ Client configured"
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To start the server:"
echo "  cd server && python3 main.py"
echo ""
echo "To start a client (in another terminal):"
echo "  cd client && python3 main.py"
echo ""
echo "To access the web interface:"
echo "  Open http://localhost:8000/web in your browser"
echo ""
echo "Your device token: $TOKEN"
echo ""
