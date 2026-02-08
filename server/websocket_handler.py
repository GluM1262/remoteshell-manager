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
