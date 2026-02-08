"""WebSocket client for RemoteShell Manager.

This module provides a WebSocket client for connecting to the RemoteShell Manager
server and sending commands.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Callable

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

# Add parent directory to path for shared imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.protocol import (
    CommandMessage,
    ResponseMessage,
    ErrorMessage,
    MessageType,
    PingMessage
)

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client for RemoteShell Manager."""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        """Initialize the WebSocket client.
        
        Args:
            host: Server hostname or IP address
            port: Server port number
        """
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}/ws"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.reconnect_delay = 5
        self.client_id: Optional[str] = None
    
    async def connect(self) -> bool:
        """Connect to the WebSocket server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to {self.uri}...")
            self.websocket = await websockets.connect(
                self.uri,
                ping_interval=20,
                ping_timeout=10
            )
            self.connected = True
            logger.info("Connected successfully")
            
            # Wait for welcome message
            try:
                welcome = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome)
                self.client_id = welcome_data.get("client_id")
                logger.info(f"Received welcome message: {welcome_data.get('message')}")
            except asyncio.TimeoutError:
                logger.warning("Did not receive welcome message")
            
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            self.connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("Disconnected from server")
            except Exception as e:
                logger.error(f"Error during disconnect: {str(e)}")
            finally:
                self.connected = False
                self.websocket = None
    
    async def send_command(self, command: str) -> Optional[dict]:
        """Send a command to the server and wait for response.
        
        Args:
            command: Shell command to execute
            
        Returns:
            Response dictionary or None if error
        """
        if not self.connected or not self.websocket:
            logger.error("Not connected to server")
            return None
        
        try:
            # Create command message
            cmd_msg = CommandMessage(command=command)
            
            # Send command
            await self.websocket.send(cmd_msg.json())
            logger.debug(f"Sent command: {command[:100]}")
            
            # Wait for response
            response = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=35.0  # Slightly longer than server timeout
            )
            
            # Parse response
            response_data = json.loads(response)
            return response_data
            
        except asyncio.TimeoutError:
            logger.error("Command execution timed out")
            return {
                "type": "error",
                "error": "Command execution timed out"
            }
        except ConnectionClosed:
            logger.error("Connection closed by server")
            self.connected = False
            return {
                "type": "error",
                "error": "Connection closed by server"
            }
        except Exception as e:
            logger.error(f"Error sending command: {str(e)}")
            return {
                "type": "error",
                "error": f"Error sending command: {str(e)}"
            }
    
    async def ping(self) -> bool:
        """Send a ping to check connection health.
        
        Returns:
            True if pong received, False otherwise
        """
        if not self.connected or not self.websocket:
            return False
        
        try:
            ping_msg = PingMessage()
            await self.websocket.send(ping_msg.json())
            
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            return response_data.get("type") == MessageType.PONG
            
        except Exception as e:
            logger.error(f"Ping failed: {str(e)}")
            return False
    
    async def auto_reconnect(self, max_attempts: int = 3) -> bool:
        """Attempt to reconnect to the server.
        
        Args:
            max_attempts: Maximum number of reconnection attempts
            
        Returns:
            True if reconnection successful, False otherwise
        """
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Reconnection attempt {attempt}/{max_attempts}")
            
            if await self.connect():
                return True
            
            if attempt < max_attempts:
                logger.info(f"Waiting {self.reconnect_delay} seconds before retry...")
                await asyncio.sleep(self.reconnect_delay)
        
        logger.error("All reconnection attempts failed")
        return False
