"""
WebSocket connection handler for device communication.
"""

import asyncio
import logging
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
"""WebSocket handler for device connections."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Optional
import logging
import json
import asyncio
from datetime import datetime

try:
    from .database import Database
    from .queue_manager import QueueManager
    from .models import WebSocketMessage
except ImportError:
    from database import Database
    from queue_manager import QueueManager
    from models import WebSocketMessage
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
    Manages active WebSocket connections to devices.
    """
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.device_metadata: Dict[str, Dict] = {}
        logger.info("Connection manager initialized")
    
    async def connect(
        self,
        device_id: str,
        websocket: WebSocket,
        metadata: Optional[Dict] = None
    ):
        """
        Register new device connection.
        
        Args:
            device_id: Unique device identifier
            websocket: WebSocket connection
            metadata: Optional device metadata
        """
        await websocket.accept()
        self.active_connections[device_id] = websocket
        self.device_metadata[device_id] = metadata or {}
        logger.info(f"Device connected: {device_id} (total: {len(self.active_connections)})")
    
    def disconnect(self, device_id: str):
        """
        Remove device connection.
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
        if device_id in self.active_connections:
            del self.active_connections[device_id]
            logger.info(f"Device disconnected: {device_id} (remaining: {len(self.active_connections)})")
        
        if device_id in self.device_metadata:
            del self.device_metadata[device_id]
    
    async def send_message(self, device_id: str, message: Dict) -> bool:
        """
        Send message to specific device.
        
        Args:
            device_id: Target device identifier
            message: Message dict to send
            
        Returns:
            True if sent successfully
        """
        if device_id not in self.active_connections:
            logger.warning(f"Cannot send to {device_id}: not connected")
            return False
        
        try:
            websocket = self.active_connections[device_id]
            await websocket.send_json(message)
            logger.debug(f"Message sent to {device_id}: {message.get('type')}")
            return True
        except Exception as e:
            logger.error(f"Error sending to {device_id}: {e}")
            self.disconnect(device_id)
            return False
    
    async def broadcast(self, message: Dict, exclude: Optional[list] = None):
        """
        Broadcast message to all connected devices.
        
        Args:
            message: Message to broadcast
            exclude: Optional list of device IDs to exclude
        """
        exclude = exclude or []
        disconnected = []
        
        for device_id, websocket in self.active_connections.items():
            if device_id in exclude:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {device_id}: {e}")
                disconnected.append(device_id)
        
        # Clean up disconnected devices
        for device_id in disconnected:
            self.disconnect(device_id)
        
        logger.info(f"Broadcast to {len(self.active_connections) - len(exclude)} devices")
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
            True if connected
            True if connected, False otherwise
        """
        return device_id in self.active_connections
    
    def get_connected_devices(self) -> list[str]:
        """
        Get list of connected device IDs.
        
        Returns:
            List of device identifiers
        """
        return list(self.active_connections.keys())
    
    def get_connection_count(self) -> int:
        """
        Get number of active connections.
        
        Returns:
            Connection count
        """
        return len(self.active_connections)
    
    def get_device_metadata(self, device_id: str) -> Optional[Dict]:
        """
        Get metadata for a device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device metadata or None
        """
        return self.device_metadata.get(device_id)


class WebSocketHandler:
    """
    Handles WebSocket communication protocol.
    """
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        security_manager,
        database,
        queue_manager,
        auth_manager
    ):
        """
        Initialize WebSocket handler.
        
        Args:
            connection_manager: Connection manager instance
            security_manager: Security manager instance
            database: Database instance
            queue_manager: Queue manager instance
            auth_manager: Auth manager instance
        """
        self.conn_mgr = connection_manager
        self.security = security_manager
        self.db = database
        self.queue = queue_manager
        self.auth = auth_manager
        logger.info("WebSocket handler initialized")
    
    async def handle_connection(self, websocket: WebSocket, token: Optional[str] = None):
        """
        Handle new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            token: Authentication token
        """
        # Validate token
        if not token or not self.auth.validate_token(token):
            await websocket.accept()
            await websocket.send_json({
                "type": "error",
                "message": "Invalid or missing authentication token"
            })
            await websocket.close()
            logger.warning("Connection rejected: invalid token")
            return
        
        # Generate device ID from token
        device_id = self.auth.get_device_id_from_token(token)
        
        # Register connection
        await self.conn_mgr.connect(device_id, websocket)
        
        # Register device in database
        await self.db.register_device(device_id=device_id, token=token)
        await self.db.update_device_status(device_id, "online")
        
        # Send welcome message
        await self.conn_mgr.send_message(device_id, {
            "type": "connected",
            "device_id": device_id,
            "message": "Connected to RemoteShell Manager"
        })
        
        # Process any queued commands
        sent_count = await self.queue.process_queued_commands(
            device_id,
            lambda msg: self.conn_mgr.send_message(device_id, msg)
        )
        
        if sent_count > 0:
            logger.info(f"Sent {sent_count} queued commands to {device_id}")
        
        try:
            # Message handling loop
            while True:
                try:
                    message_text = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    message = json.loads(message_text)
                    await self._handle_message(device_id, message)
                except asyncio.TimeoutError:
                    # Normal timeout, continue
                    continue
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break
        
        except WebSocketDisconnect:
            logger.info(f"Device disconnected: {device_id}")
        except Exception as e:
            logger.error(f"Error handling device {device_id}: {e}")
        finally:
            self.conn_mgr.disconnect(device_id)
            await self.db.update_device_status(device_id, "offline")
    
    async def _handle_message(self, device_id: str, message: Dict):
        """
        Handle incoming message from device.
        
        Args:
            device_id: Source device identifier
            message: Message dict
        """
        msg_type = message.get("type")
        
        if msg_type == "command_result":
            # Store command result in database
            await self.db.add_command_history(
                device_id=device_id,
                command=message.get("command", ""),
                status="completed",
                stdout=message.get("stdout", ""),
                stderr=message.get("stderr", ""),
                exit_code=message.get("exit_code"),
                execution_time=message.get("execution_time")
            )
            logger.info(f"Command result stored for {device_id}")
        
        elif msg_type == "ping":
            # Respond to ping
            await self.conn_mgr.send_message(device_id, {
                "type": "pong",
                "timestamp": message.get("timestamp")
            })
        
        elif msg_type == "status":
            # Update device status/metadata
            metadata = message.get("metadata", {})
            self.conn_mgr.device_metadata[device_id] = metadata
            logger.debug(f"Status update from {device_id}")
        
        else:
            logger.warning(f"Unknown message type from {device_id}: {msg_type}")
            List of device IDs
        """
        return list(self.active_connections.keys())
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
