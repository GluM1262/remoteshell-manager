#!/bin/bash
#
# RemoteShell Client Installation Script
# Installs and configures RemoteShell client as a systemd service
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/remoteshell"
CONFIG_DIR="/etc/remoteshell"
LOG_DIR="/var/log/remoteshell"
SERVICE_USER="remoteshell"
SERVICE_GROUP="remoteshell"
PYTHON_MIN_VERSION="3.9"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_python() {
    print_info "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    python_version=$(python3 --version | awk '{print $2}')
    print_info "Found Python $python_version"
    
    # Check minimum version
    required_version="$PYTHON_MIN_VERSION"
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= tuple(map(int, '$required_version'.split('.'))) else 1)"; then
        print_error "Python $required_version or higher is required"
        exit 1
    fi
}

create_user() {
    print_info "Creating service user..."
    
    if id "$SERVICE_USER" &>/dev/null; then
        print_warn "User $SERVICE_USER already exists"
    else
        useradd --system --no-create-home --shell /bin/false "$SERVICE_USER"
        print_info "Created user $SERVICE_USER"
    fi
}

create_directories() {
    print_info "Creating directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    
    print_info "Directories created"
}

install_dependencies() {
    print_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        print_info "Dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

copy_files() {
    print_info "Copying client files..."
    
    # Copy Python files
    cp -r *.py "$INSTALL_DIR/client/"
    
    # Copy config template
    if [ -f "config.yaml.example" ]; then
        if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
            cp config.yaml.example "$CONFIG_DIR/config.yaml"
            print_info "Config template copied to $CONFIG_DIR/config.yaml"
            print_warn "Please edit $CONFIG_DIR/config.yaml with your settings"
        else
            print_warn "Config file already exists, skipping"
        fi
    fi
    
    print_info "Files copied"
}

install_systemd_service() {
    print_info "Installing systemd service..."
    
    if [ -f "systemd/remoteshell-client.service" ]; then
        cp systemd/remoteshell-client.service /etc/systemd/system/
        
        if [ -f "systemd/remoteshell-client.env" ]; then
            cp systemd/remoteshell-client.env "$CONFIG_DIR/client.env"
        fi
        
        systemctl daemon-reload
        print_info "Systemd service installed"
    else
        print_error "Service file not found"
        exit 1
    fi
}

set_permissions() {
    print_info "Setting permissions..."
    
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$LOG_DIR"
    chown -R "$SERVICE_USER:$SERVICE_GROUP" "$CONFIG_DIR"
    
    # Secure config file
    chmod 600 "$CONFIG_DIR/config.yaml"
    
    print_info "Permissions set"
}

enable_service() {
    print_info "Enabling service..."
    
    systemctl enable remoteshell-client.service
    print_info "Service enabled"
}

# Main installation process
main() {
    echo "======================================"
    echo "RemoteShell Client Installation"
    echo "======================================"
    echo
    
    check_root
    check_python
    create_user
    create_directories
    install_dependencies
    copy_files
    install_systemd_service
    set_permissions
    enable_service
    
    echo
    echo "======================================"
    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo "======================================"
    echo
    echo "Next steps:"
    echo "1. Edit configuration: nano $CONFIG_DIR/config.yaml"
    echo "2. Start service: systemctl start remoteshell-client"
    echo "3. Check status: systemctl status remoteshell-client"
    echo "4. View logs: journalctl -u remoteshell-client -f"
    echo
}

main "$@"
