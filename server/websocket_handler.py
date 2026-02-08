"""
WebSocket Handler

Manages WebSocket connections, device registry, and message routing.
"""

import logging
import json
from typing import Dict
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from server.models import CommandMessage, ResponseMessage, ErrorMessage, DeviceInfo
from server.shell_executor import execute_command
from server.config import settings
import asyncio
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
    """
    Manages WebSocket connections for multiple devices.
    
    Maintains a registry of connected devices and handles message routing.
    """
    
    def __init__(self):
        # Map of device_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Map of device_id -> DeviceInfo
        self.device_info: Dict[str, DeviceInfo] = {}
    
    async def connect(self, device_id: str, websocket: WebSocket):
        """
        Register a new device connection.
        
        Args:
            device_id: Unique device identifier
            websocket: WebSocket connection object
        """
        await websocket.accept()
        self.active_connections[device_id] = websocket
        self.device_info[device_id] = DeviceInfo(
            device_id=device_id,
            connected_at=datetime.now(timezone.utc)
        )
        logger.info(f"Device {device_id} connected. Total devices: {len(self.active_connections)}")
    
    def disconnect(self, device_id: str):
        """
        Remove device from registry.
        
        Args:
            device_id: Device identifier to disconnect
        """
        if device_id in self.active_connections:
            del self.active_connections[device_id]
        if device_id in self.device_info:
            del self.device_info[device_id]
        logger.info(f"Device {device_id} disconnected. Total devices: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, device_id: str):
        """
        Send message to a specific device.
        
        Args:
            message: JSON message string
            device_id: Target device identifier
        """
        if device_id in self.active_connections:
            websocket = self.active_connections[device_id]
            await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """
        Send message to all connected devices.
        
        Args:
            message: JSON message string
        """
        for device_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message to {device_id}: {e}")
    
    def get_connected_devices(self) -> list:
        """
        Get list of all connected devices with their information.
        
        Returns:
            List of DeviceInfo objects
        """
        return [info.model_dump() for info in self.device_info.values()]


# Global connection manager instance
manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket, device_id: str):
    """
    Handle WebSocket connection for a device.
    
    Connection flow:
    1. Accept connection and register device
    2. Listen for incoming messages
    3. Process command messages
    4. Send responses back
    5. Handle disconnection and cleanup
    
    Args:
        websocket: WebSocket connection
        device_id: Authenticated device identifier
    """
    await manager.connect(device_id, websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.debug(f"Received from {device_id}: {data[:100]}")
            
            try:
                # Parse incoming message
                message_dict = json.loads(data)
                
                # Validate message type
                if message_dict.get("type") == "command":
                    # Parse command message
                    cmd_msg = CommandMessage(**message_dict)
                    
                    # Update last command time
                    if device_id in manager.device_info:
                        manager.device_info[device_id].last_command = datetime.now(timezone.utc)
                    
                    # Execute command with timeout
                    timeout = cmd_msg.timeout or settings.command_timeout
                    
                    logger.info(f"Executing command from {device_id}: {cmd_msg.command}")
                    
                    try:
                        result = await execute_command(cmd_msg.command, timeout=timeout)
                        
                        # Create response message
                        response = ResponseMessage(
                            type="response",
                            id=cmd_msg.id,
                            stdout=result["stdout"],
                            stderr=result["stderr"],
                            exit_code=result["exit_code"],
                            execution_time=result["execution_time"]
                        )
                        
                        # Send response back to client
                        await manager.send_personal_message(
                            response.model_dump_json(),
                            device_id
                        )
                        
                    except asyncio.TimeoutError as e:
                        # Command timed out
                        error_msg = ErrorMessage(
                            type="error",
                            message=f"Command timed out after {timeout} seconds"
                        )
                        await manager.send_personal_message(
                            error_msg.model_dump_json(),
                            device_id
                        )
                    
                    except ValueError as e:
                        # Security validation failed
                        error_msg = ErrorMessage(
                            type="error",
                            message=str(e)
                        )
                        await manager.send_personal_message(
                            error_msg.model_dump_json(),
                            device_id
                        )
                    
                    except Exception as e:
                        # Other execution errors
                        logger.error(f"Command execution error: {e}")
                        error_msg = ErrorMessage(
                            type="error",
                            message=f"Command execution failed: {str(e)}"
                        )
                        await manager.send_personal_message(
                            error_msg.model_dump_json(),
                            device_id
                        )
                
                else:
                    # Unknown message type
                    error_msg = ErrorMessage(
                        type="error",
                        message=f"Unknown message type: {message_dict.get('type')}"
                    )
                    await manager.send_personal_message(
                        error_msg.model_dump_json(),
                        device_id
                    )
            
            except json.JSONDecodeError:
                # Invalid JSON
                error_msg = ErrorMessage(
                    type="error",
                    message="Invalid JSON format"
                )
                await manager.send_personal_message(
                    error_msg.model_dump_json(),
                    device_id
                )
            
            except Exception as e:
                # Message parsing/validation error
                logger.error(f"Message processing error: {e}")
                error_msg = ErrorMessage(
                    type="error",
                    message=f"Message processing failed: {str(e)}"
                )
                await manager.send_personal_message(
                    error_msg.model_dump_json(),
                    device_id
                )
    
    except WebSocketDisconnect:
        logger.info(f"Device {device_id} disconnected normally")
        manager.disconnect(device_id)
    
    except Exception as e:
        logger.error(f"WebSocket error for {device_id}: {e}")
        manager.disconnect(device_id)
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
