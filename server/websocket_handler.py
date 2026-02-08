"""WebSocket handler for device connections."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Optional
import logging
import json
import asyncio
from datetime import datetime

from .database import Database
from .queue_manager import QueueManager
from .models import WebSocketMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for devices."""
    
    def __init__(self, database: Database, queue_manager: QueueManager):
        """
        Initialize connection manager.
        
        Args:
            database: Database instance
            queue_manager: Queue manager instance
        """
        self.active_connections: Dict[str, WebSocket] = {}
        self.database = database
        self.queue_manager = queue_manager
        self._locks: Dict[str, asyncio.Lock] = {}
    
    def _get_lock(self, device_id: str) -> asyncio.Lock:
        """Get or create lock for device."""
        if device_id not in self._locks:
            self._locks[device_id] = asyncio.Lock()
        return self._locks[device_id]
    
    async def connect(self, device_id: str, device_token: str, websocket: WebSocket) -> bool:
        """
        Connect device and start processing.
        
        Args:
            device_id: Device identifier
            device_token: Device authentication token
            websocket: WebSocket connection
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            lock = self._get_lock(device_id)
            async with lock:
                # Authenticate device
                if not await self._authenticate_device(device_id, device_token):
                    logger.warning(f"Authentication failed for device {device_id}")
                    return False
                
                # Disconnect existing connection if any
                if device_id in self.active_connections:
                    logger.info(f"Disconnecting existing connection for device {device_id}")
                    await self.disconnect(device_id)
                
                # Accept WebSocket connection
                await websocket.accept()
                
                # Register device as online
                await self.database.register_device(device_id, device_token)
                await self.database.update_device_status(device_id, "online")
                
                # Store connection
                self.active_connections[device_id] = websocket
                
                # Start queue processing
                await self.queue_manager.start_processing(device_id, websocket)
                
                logger.info(f"Device {device_id} connected successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to connect device {device_id}: {e}")
            return False
    
    async def disconnect(self, device_id: str) -> None:
        """
        Disconnect device and cleanup.
        
        Args:
            device_id: Device identifier
        """
        try:
            lock = self._get_lock(device_id)
            async with lock:
                # Stop queue processing
                await self.queue_manager.stop_processing(device_id)
                
                # Update device status
                await self.database.update_device_status(device_id, "offline")
                
                # Remove connection
                if device_id in self.active_connections:
                    websocket = self.active_connections[device_id]
                    try:
                        await websocket.close()
                    except Exception:
                        pass  # Connection might already be closed
                    del self.active_connections[device_id]
                
                logger.info(f"Device {device_id} disconnected")
                
        except Exception as e:
            logger.error(f"Error disconnecting device {device_id}: {e}")
    
    async def handle_message(self, device_id: str, message: dict) -> None:
        """
        Handle incoming message from device.
        
        Args:
            device_id: Device identifier
            message: Message data
        """
        try:
            msg_type = message.get("type")
            
            if msg_type == "result":
                # Command execution result
                await self._handle_command_result(device_id, message)
            elif msg_type == "ping":
                # Keep-alive ping
                await self._handle_ping(device_id)
            elif msg_type == "error":
                # Error from device
                await self._handle_error(device_id, message)
            else:
                logger.warning(f"Unknown message type from device {device_id}: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling message from device {device_id}: {e}")
    
    async def _authenticate_device(self, device_id: str, device_token: str) -> bool:
        """
        Authenticate device credentials.
        
        Args:
            device_id: Device identifier
            device_token: Device token
            
        Returns:
            True if authenticated, False otherwise
        """
        try:
            # Get device info from database
            device_info = await self.database.get_device_info(device_id)
            
            if device_info:
                # Verify token
                return device_info['device_token'] == device_token
            else:
                # New device - accept and register
                logger.info(f"Registering new device {device_id}")
                return True
                
        except Exception as e:
            logger.error(f"Authentication error for device {device_id}: {e}")
            return False
    
    async def _handle_command_result(self, device_id: str, message: dict) -> None:
        """
        Handle command execution result.
        
        Args:
            device_id: Device identifier
            message: Result message
        """
        try:
            command_id = message.get("command_id")
            stdout = message.get("stdout", "")
            stderr = message.get("stderr", "")
            exit_code = message.get("exit_code", -1)
            execution_time = message.get("execution_time", 0.0)
            
            if not command_id:
                logger.warning(f"Result message missing command_id from device {device_id}")
                return
            
            # Update command status
            if exit_code == 0:
                await self.queue_manager.complete_command(
                    command_id, stdout, stderr, exit_code, execution_time
                )
            else:
                await self.queue_manager.fail_command(
                    command_id, f"Command exited with code {exit_code}"
                )
            
            logger.debug(f"Processed result for command {command_id}")
            
        except Exception as e:
            logger.error(f"Error handling command result: {e}")
    
    async def _handle_ping(self, device_id: str) -> None:
        """
        Handle keep-alive ping.
        
        Args:
            device_id: Device identifier
        """
        try:
            # Send pong response
            websocket = self.active_connections.get(device_id)
            if websocket:
                await websocket.send_json({"type": "pong"})
            
            # Update last connected timestamp
            await self.database.update_device_status(device_id, "online")
            
        except Exception as e:
            logger.error(f"Error handling ping from device {device_id}: {e}")
    
    async def _handle_error(self, device_id: str, message: dict) -> None:
        """
        Handle error from device.
        
        Args:
            device_id: Device identifier
            message: Error message
        """
        try:
            command_id = message.get("command_id")
            error = message.get("error", "Unknown error")
            
            if command_id:
                await self.queue_manager.fail_command(command_id, error)
            
            logger.warning(f"Error from device {device_id}: {error}")
            
        except Exception as e:
            logger.error(f"Error handling error message: {e}")
    
    async def send_command(self, device_id: str, command_id: str, command: str, timeout: int) -> bool:
        """
        Send command to device.
        
        Args:
            device_id: Device identifier
            command_id: Command identifier
            command: Command to execute
            timeout: Command timeout
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            websocket = self.active_connections.get(device_id)
            if not websocket:
                logger.warning(f"Device {device_id} not connected")
                return False
            
            await websocket.send_json({
                "type": "command",
                "command_id": command_id,
                "command": command,
                "timeout": timeout
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending command to device {device_id}: {e}")
            return False
    
    def is_connected(self, device_id: str) -> bool:
        """
        Check if device is connected.
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if connected, False otherwise
        """
        return device_id in self.active_connections
    
    def get_connected_devices(self) -> list[str]:
        """
        Get list of connected device IDs.
        
        Returns:
            List of device IDs
        """
        return list(self.active_connections.keys())
