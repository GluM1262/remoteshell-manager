#!/usr/bin/env python3
"""
Integration test for RemoteShell Manager.

Tests the complete flow:
1. Device connects via WebSocket
2. Server sends command
3. Device executes and returns result
4. Result is stored in database
"""

import asyncio
import json
import requests
import websockets
import time

import os
import uuid

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
WS_URL = os.getenv("WS_URL", "ws://localhost:8000")
DEVICE_ID = os.getenv("TEST_DEVICE_ID", f"test_device_{uuid.uuid4().hex[:8]}")
DEVICE_TOKEN = os.getenv("TEST_DEVICE_TOKEN", uuid.uuid4().hex)



async def test_device_connection():
    """Test device connection and command execution."""
    
    print("=== RemoteShell Manager Integration Test ===\n")
    
    # 1. Connect device via WebSocket
    print(f"1. Connecting device {DEVICE_ID}...")
    ws_url = f"{WS_URL}/ws/{DEVICE_ID}?token={DEVICE_TOKEN}"
    
    async with websockets.connect(ws_url) as websocket:
        print(f"   ✓ Device connected\n")
        
        # 2. Send test command via API
        print("2. Sending command via API...")
        response = requests.post(
            f"{SERVER_URL}/api/command",
            json={
                "device_id": DEVICE_ID,
                "command": "echo 'Hello from RemoteShell Manager'",
                "timeout": 30
            }
        )
        command_data = response.json()
        command_id = command_data["command_id"]
        print(f"   ✓ Command queued: {command_id}\n")
        
        # 3. Device receives command
        print("3. Device waiting for command...")
        message = await websocket.recv()
        cmd_msg = json.loads(message)
        print(f"   ✓ Received command: {cmd_msg['command']}\n")
        
        # 4. Device executes command
        print("4. Executing command...")
        result = {
            "type": "result",
            "command_id": cmd_msg["command_id"],
            "stdout": "Hello from RemoteShell Manager\n",
            "stderr": "",
            "exit_code": 0,
            "execution_time": 0.01
        }
        await websocket.send(json.dumps(result))
        print(f"   ✓ Result sent\n")
        
        # 5. Wait for database update
        print("5. Waiting for database update...")
        await asyncio.sleep(2)
        
        # 6. Check command status via API
        print("6. Checking command status...")
        response = requests.get(f"{SERVER_URL}/api/command/{command_id}")
        status = response.json()
        print(f"   Status: {status['status']}")
        print(f"   Exit Code: {status['exit_code']}")
        print(f"   Stdout: {status['stdout'].strip()}\n")
        
        # 7. Check device info
        print("7. Checking device info...")
        response = requests.get(f"{SERVER_URL}/api/devices/{DEVICE_ID}")
        device = response.json()
        print(f"   Status: {device['status']}")
        print(f"   Total Commands: {device['total_commands']}\n")
        
        # 8. Check statistics
        print("8. Checking statistics...")
        response = requests.get(f"{SERVER_URL}/api/statistics")
        stats = response.json()
        print(f"   Total Commands: {stats['total_commands']}")
        print(f"   Completed: {stats['completed']}")
        print(f"   Failed: {stats['failed']}\n")
        
        # 9. Send another command to test queue
        print("9. Testing command queue with multiple commands...")
        commands = []
        for i in range(3):
            response = requests.post(
                f"{SERVER_URL}/api/command",
                json={
                    "device_id": DEVICE_ID,
                    "command": f"echo 'Command {i+1}'",
                    "timeout": 30
                }
            )
            cmd = response.json()
            commands.append(cmd["command_id"])
            print(f"   ✓ Queued: {cmd['command_id']}")
        
        # Process queued commands
        print("\n10. Processing queued commands...")
        for i, cmd_id in enumerate(commands):
            message = await websocket.recv()
            cmd_msg = json.loads(message)
            
            result = {
                "type": "result",
                "command_id": cmd_msg["command_id"],
                "stdout": f"Command {i+1}\n",
                "stderr": "",
                "exit_code": 0,
                "execution_time": 0.01
            }
            await websocket.send(json.dumps(result))
            print(f"   ✓ Processed: {cmd_msg['command_id']}")
        
        # Wait for database updates
        await asyncio.sleep(2)
        
        # 11. Check final statistics
        print("\n11. Final statistics...")
        response = requests.get(f"{SERVER_URL}/api/devices/{DEVICE_ID}/statistics")
        stats = response.json()
        print(f"   Total Commands: {stats['total_commands']}")
        print(f"   Completed: {stats['completed']}")
        print(f"   Avg Execution Time: {stats['avg_execution_time']:.3f}s\n")
        
        # 12. Test history export
        print("12. Testing history export...")
        response = requests.get(f"{SERVER_URL}/api/history/export?format=json&device_id={DEVICE_ID}&limit=10")
        history = response.json()
        print(f"   ✓ Exported {len(history)} commands\n")
        
        print("=== All tests passed! ===")


async def main():
    """Main test function."""
    try:
        await test_device_connection()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
