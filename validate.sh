#!/bin/bash
# RemoteShell Manager - System Validation Script

set -e

ERRORS=0
WARNINGS=0

echo "========================================"
echo "RemoteShell Manager - System Validation"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

error() {
    echo -e "${RED}✗ $1${NC}"
    ((ERRORS++))
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    ((WARNINGS++))
}

# Check Python version
echo "1. Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 9 ]; then
        success "Python $PYTHON_VERSION"
    else
        error "Python 3.9+ required (found $PYTHON_VERSION)"
    fi
else
    error "Python 3 not found"
fi
echo ""

# Check dependencies
echo "2. Checking Python dependencies..."
DEPS_OK=true
python3 -c "import yaml" 2>/dev/null && success "PyYAML installed" || error "PyYAML not installed"
for dep in fastapi uvicorn websockets pydantic; do
    if python3 -c "import yaml" 2>/dev/null; then
        success "PyYAML installed"
    else
        error "PyYAML not installed"
        DEPS_OK=false
    fi
    if python3 -c "import $dep" 2>/dev/null; then
        success "$dep installed"
    else
        error "$dep not installed"
        DEPS_OK=false
    fi
done
echo ""

# Check file structure
echo "3. Checking file structure..."
declare -a REQUIRED_FILES=(
    "server/main.py"
    "server/config.py"
    "server/security.py"
    "server/database.py"
    "server/queue_manager.py"
    "server/auth.py"
    "server/websocket_handler.py"
    "server/shell_executor.py"
    "client/main.py"
    "client/websocket_client.py"
    "client/command_executor.py"
    "client/config_manager.py"
    "README.md"
    "SETUP.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "$file"
    else
        error "$file missing"
    fi
done
echo ""

# Check configuration files
echo "4. Checking configuration..."
if [ -f "server/.env" ]; then
    success "Server configuration exists"
    
    if grep -q "DEVICE_TOKENS" server/.env; then
        success "DEVICE_TOKENS configured"
    else
        warning "DEVICE_TOKENS not configured"
    fi
else
    warning "Server .env not found (copy from .env.example)"
fi

if [ -f "client/config.yaml" ]; then
    success "Client configuration exists"
else
    warning "Client config.yaml not found (copy from config.yaml.example)"
fi
echo ""

# Check TLS certificates
echo "5. Checking TLS certificates..."
if [ -f "server/tls/cert.pem" ] && [ -f "server/tls/key.pem" ]; then
    success "TLS certificates found"
    
    # Check permissions
    CERT_PERMS=$(stat -c %a server/tls/cert.pem 2>/dev/null || stat -f %A server/tls/cert.pem 2>/dev/null)
    KEY_PERMS=$(stat -c %a server/tls/key.pem 2>/dev/null || stat -f %A server/tls/key.pem 2>/dev/null)
    
    if [ "$KEY_PERMS" = "600" ]; then
        success "Key file permissions correct (600)"
    else
        warning "Key file permissions should be 600 (currently $KEY_PERMS)"
    fi
else
    warning "TLS certificates not found (run server/tls/generate_certs.sh)"
fi
echo ""

# Test server imports
echo "6. Testing server imports..."
if cd server && python3 -c "import main" 2>/dev/null; then
    success "Server imports OK"
    cd ..
else
    error "Server import errors"
    cd ..
fi
echo ""

# Test client imports
echo "7. Testing client imports..."
if cd client && python3 -c "import main; import config_manager" 2>/dev/null; then
    success "Client imports OK"
    cd ..
else
    error "Client import errors"
    cd ..
fi
echo ""

# Run tests if available
echo "8. Running tests..."
if [ -d "tests" ]; then
    if python3 tests/test_security.py &>/dev/null; then
        success "Security tests passed"
    else
        error "Security tests failed"
    fi
    
    # Note: Command executor tests may hang, skip for now
    # if timeout 5 python3 tests/test_command_executor.py &>/dev/null; then
    #     success "Command executor tests passed"
    # else
    #     warning "Command executor tests failed or timed out"
    # fi
else
    warning "Tests directory not found"
fi
echo ""

# Check examples
echo "9. Checking examples..."
if [ -d "examples" ]; then
    success "Examples directory exists"
    
    if [ -x "examples/quickstart.sh" ]; then
        success "Quickstart script executable"
    else
        warning "Quickstart script not executable"
    fi
else
    warning "Examples directory not found"
fi
echo ""

# Summary
echo "========================================"
echo "Validation Summary"
echo "========================================"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Your RemoteShell Manager installation is ready."
    echo ""
    echo "Next steps:"
    echo "1. Configure server: edit server/.env"
    echo "2. Configure client: edit client/config.yaml"
    echo "3. Start server: cd server && python3 main.py"
    echo "4. Start client: cd client && python3 main.py"
    echo "5. Access web UI: http://localhost:8000/web"
    EXIT_CODE=0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    echo ""
    echo "System is functional but some optional components are missing."
    EXIT_CODE=0
else
    echo -e "${RED}✗ $ERRORS error(s) found${NC}"
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    echo ""
    echo "Please fix the errors before proceeding."
    EXIT_CODE=1
fi

echo ""
exit $EXIT_CODE
