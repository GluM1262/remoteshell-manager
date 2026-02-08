#!/bin/bash
#
# RemoteShell Client Uninstallation Script
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}[ERROR]${NC} This script must be run as root"
        exit 1
    fi
}

main() {
    echo "======================================"
    echo "RemoteShell Client Uninstallation"
    echo "======================================"
    echo
    
    check_root
    
    print_info "Stopping service..."
    systemctl stop remoteshell-client.service || true
    
    print_info "Disabling service..."
    systemctl disable remoteshell-client.service || true
    
    print_info "Removing service file..."
    rm -f /etc/systemd/system/remoteshell-client.service
    systemctl daemon-reload
    
    print_info "Removing files..."
    rm -rf /opt/remoteshell
    
    print_warn "Keeping configuration and logs (remove manually if needed):"
    print_warn "  - /etc/remoteshell"
    print_warn "  - /var/log/remoteshell"
    
    print_info "Removing user..."
    userdel remoteshell || true
    
    echo
    echo -e "${GREEN}Uninstallation completed${NC}"
    echo
}

main "$@"
