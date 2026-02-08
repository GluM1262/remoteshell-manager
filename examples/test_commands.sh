#!/bin/bash
# Test script for RemoteShell Manager commands

echo "========================================"
echo "RemoteShell Manager - Command Tests"
echo "========================================"
echo ""

API_BASE="${API_BASE:-http://localhost:8000}"
DEVICE_ID="${1:-}"

if [ -z "$DEVICE_ID" ]; then
    echo "Usage: $0 <device_id>"
    echo ""
    echo "Available devices:"
    curl -s "$API_BASE/api/devices" | python3 -m json.tool | grep device_id || echo "No devices found"
    exit 1
fi

echo "Testing commands on device: $DEVICE_ID"
echo "API Base: $API_BASE"
echo ""

# Test commands
declare -a COMMANDS=(
    "whoami"
    "hostname"
    "pwd"
    "ls -la"
    "uptime"
    "date"
)

for cmd in "${COMMANDS[@]}"; do
    echo "Testing: $cmd"
    RESPONSE=$(curl -s -X POST "$API_BASE/api/devices/$DEVICE_ID/command?command=$(echo "$cmd" | jq -sRr @uri)")
    echo "Response: $RESPONSE"
    echo ""
    sleep 1
done

echo "========================================"
echo "Command Tests Complete"
echo "========================================"
echo ""
echo "View history:"
echo "  curl -s $API_BASE/api/devices/$DEVICE_ID/history | python3 -m json.tool"
echo ""
