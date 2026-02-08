#!/usr/bin/env python3
"""
Example device client for RemoteShell Manager.

This script demonstrates how a device connects to the server and executes commands.
"""

import asyncio
import json
import subprocess
import time
import websockets
import argparse
import logging
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeviceClient:
    """Simple device client implementation."""
    
    def __init__(self, server_url: str, device_id: str, device_token: str):
        """
        Initialize device client.
        
        Args:
            server_url: WebSocket server URL (e.g., ws://localhost:8000)
            device_id: Device identifier
            device_token: Authentication token
        """
        self.server_url = server_url
        self.device_id = device_id
        self.device_token = device_token
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
    
    async def connect(self) -> None:
        """Connect to server."""
        ws_url = f"{self.server_url}/ws/{self.device_id}?token={self.device_token}"
        logger.info(f"Connecting to {ws_url}")
        
        try:
            self.websocket = await websockets.connect(ws_url)
            logger.info("Connected to server")
            self.running = True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from server."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from server")
    
    async def execute_command(self, command: str, timeout: int = 30) -> dict:
        """
        Execute shell command.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Result dictionary with stdout, stderr, exit_code, execution_time
        """
        logger.info(f"Executing command: {command}")
        start_time = time.time()
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "execution_time": execution_time
            }
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return {
                "stdout": "",
                "stderr": "Command timed out",
                "exit_code": -1,
                "execution_time": execution_time
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "execution_time": execution_time
            }
    
    async def handle_message(self, message: dict) -> None:
        """
        Handle incoming message from server.
        
        Args:
            message: Message data
        """
        msg_type = message.get("type")
        
        if msg_type == "command":
            # Execute command
            command_id = message.get("command_id")
            command = message.get("command")
            timeout = message.get("timeout", 30)
            
            logger.info(f"Received command {command_id}: {command}")
            
            # Execute
            result = await self.execute_command(command, timeout)
            
            # Send result back
            await self.websocket.send(json.dumps({
                "type": "result",
                "command_id": command_id,
                **result
            }))
            
            logger.info(f"Sent result for command {command_id}: exit_code={result['exit_code']}")
            
        elif msg_type == "pong":
            # Keep-alive response
            logger.debug("Received pong")
        else:
            logger.warning(f"Unknown message type: {msg_type}")
    
    async def send_ping(self) -> None:
        """Send keep-alive ping to server."""
        try:
            if self.websocket:
                await self.websocket.send(json.dumps({"type": "ping"}))
                logger.debug("Sent ping")
        except Exception as e:
            logger.error(f"Failed to send ping: {e}")
    
    async def run(self) -> None:
        """Run client main loop."""
        await self.connect()
        
        # Start ping task
        async def ping_loop():
            while self.running:
                await asyncio.sleep(30)
                if self.running:
                    await self.send_ping()
        
        ping_task = asyncio.create_task(ping_loop())
        
        try:
            # Listen for messages
            async for message_text in self.websocket:
                try:
                    message = json.loads(message_text)
                    await self.handle_message(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.running = False
            ping_task.cancel()
            await self.disconnect()


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="RemoteShell Manager Device Client")
    parser.add_argument(
        "--server",
        default="ws://localhost:8000",
        help="Server URL (default: ws://localhost:8000)"
    )
    parser.add_argument(
        "--device-id",
        required=True,
        help="Device identifier"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Device authentication token"
    )
    
    args = parser.parse_args()
    
    # Create and run client
    client = DeviceClient(args.server, args.device_id, args.token)
    
    try:
        await client.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
