"""
WebSocket connection handler for device communication.
"""

import asyncio
import logging
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json

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
    
    def is_connected(self, device_id: str) -> bool:
        """
        Check if device is connected.
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if connected
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
