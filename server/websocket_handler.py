"""WebSocket connection handler for RemoteShell Manager.

This module manages WebSocket connections and handles incoming commands
from clients.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Set

from fastapi import WebSocket, WebSocketDisconnect

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.shell_executor import ShellExecutor
from shared.protocol import (
    CommandMessage,
    ResponseMessage,
    ErrorMessage,
    MessageType,
    PingMessage,
    PongMessage
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and message routing."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.shell_executor = ShellExecutor(timeout=30)
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            client_id: Unique identifier for the client
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str) -> None:
        """Remove a disconnected client.
        
        Args:
            client_id: Unique identifier for the client
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, websocket: WebSocket, message: dict) -> None:
        """Send a message to a specific client.
        
        Args:
            websocket: The WebSocket connection
            message: Message dictionary to send
        """
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise
    
    async def handle_command(self, websocket: WebSocket, data: dict, client_id: str) -> None:
        """Handle an incoming command from a client.
        
        Args:
            websocket: The WebSocket connection
            data: Command data received from client
            client_id: Unique identifier for the client
        """
        try:
            # Parse command message
            command_msg = CommandMessage(**data)
            command = command_msg.command
            
            logger.info(f"Received command from {client_id}: {command[:100]}")
            
            # Validate command
            is_valid, error_msg = self.shell_executor.validate_command(command)
            if not is_valid:
                error_response = ErrorMessage(
                    error=f"Invalid command: {error_msg}"
                )
                await self.send_message(websocket, error_response.model_dump(mode='json'))
                return
            
            # Execute command
            stdout, stderr, exit_code = await self.shell_executor.execute(command)
            
            # Send response
            response = ResponseMessage(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code
            )
            await self.send_message(websocket, response.model_dump(mode='json'))
            
        except Exception as e:
            logger.error(f"Error handling command from {client_id}: {str(e)}")
            error_response = ErrorMessage(
                error=f"Error processing command: {str(e)}"
            )
            await self.send_message(websocket, error_response.model_dump(mode='json'))
    
    async def handle_ping(self, websocket: WebSocket) -> None:
        """Handle a ping message.
        
        Args:
            websocket: The WebSocket connection
        """
        pong = PongMessage()
        await self.send_message(websocket, pong.model_dump(mode='json'))
    
    async def handle_message(self, websocket: WebSocket, message: str, client_id: str) -> None:
        """Route incoming messages to appropriate handlers.
        
        Args:
            websocket: The WebSocket connection
            message: Raw message string from client
            client_id: Unique identifier for the client
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == MessageType.COMMAND:
                await self.handle_command(websocket, data, client_id)
            elif message_type == MessageType.PING:
                await self.handle_ping(websocket)
            else:
                logger.warning(f"Unknown message type from {client_id}: {message_type}")
                error_response = ErrorMessage(
                    error=f"Unknown message type: {message_type}"
                )
                await self.send_message(websocket, error_response.model_dump(mode='json'))
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {client_id}: {str(e)}")
            error_response = ErrorMessage(
                error=f"Invalid JSON: {str(e)}"
            )
            await self.send_message(websocket, error_response.model_dump(mode='json'))
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {str(e)}")
            error_response = ErrorMessage(
                error=f"Error handling message: {str(e)}"
            )
            await self.send_message(websocket, error_response.model_dump(mode='json'))
