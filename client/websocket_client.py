"""
WebSocket client with TLS support.
"""

import asyncio
import websockets
import json
import logging
import ssl
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client for RemoteShell with TLS support."""
    
    def __init__(self, config):
        """
        Initialize WebSocket client.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.websocket = None
        self.connected = False
        
        # Build WebSocket URL
        server_config = getattr(config, 'server', None)
        if server_config:
            self.url = getattr(server_config, 'url', 'ws://localhost:8000/ws')
            self.token = getattr(server_config, 'token', '')
            self.use_ssl = getattr(server_config, 'use_ssl', False)
        else:
            self.url = 'ws://localhost:8000/ws'
            self.token = ''
            self.use_ssl = False
        
        # Add token to URL
        if self.token:
            separator = '&' if '?' in self.url else '?'
            self.url = f"{self.url}{separator}token={self.token}"
        
        # SSL configuration
        security_config = getattr(config, 'security', None)
        if security_config:
            self.validate_ssl = getattr(security_config, 'validate_ssl', True)
        else:
            self.validate_ssl = True
    
    def _create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """
        Create SSL context for TLS connections.
        
        Returns:
            SSL context if TLS is enabled, None otherwise
        """
        if not self.use_ssl:
            return None
        
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        
        if self.validate_ssl:
            # Validate server certificate
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.load_default_certs()
        else:
            # Allow self-signed certificates (development only)
            logger.warning("⚠️  SSL certificate validation disabled (development only)")
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        # Set secure TLS parameters
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        return ssl_context
    
    async def connect(self):
        """Connect to WebSocket server."""
        try:
            ssl_context = self._create_ssl_context()
            
            logger.info(f"Connecting to {self.url}")
            if self.use_ssl:
                logger.info("TLS encryption enabled")
            
            self.websocket = await websockets.connect(
                self.url,
                ssl=ssl_context
            )
            
            self.connected = True
            logger.info("Connected to server")
            
            # Wait for welcome message
            message = await self.websocket.recv()
            data = json.loads(message)
            logger.info(f"Server message: {data}")
            
            return True
        
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            return False
    
    async def send_command(self, command: str, timeout: Optional[int] = None):
        """
        Send command to server.
        
        Args:
            command: Command to execute
            timeout: Optional execution timeout
        """
        if not self.connected or not self.websocket:
            logger.error("Not connected to server")
            return
        
        try:
            message = {
                "type": "command",
                "command": command
            }
            
            if timeout is not None:
                message["timeout"] = timeout
            
            await self.websocket.send(json.dumps(message))
            logger.info(f"Command sent: {command}")
        
        except Exception as e:
            logger.error(f"Error sending command: {e}")
    
    async def receive_message(self):
        """
        Receive message from server.
        
        Returns:
            Parsed JSON message or None
        """
        if not self.connected or not self.websocket:
            return None
        
        try:
            message = await self.websocket.recv()
            return json.loads(message)
        
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    async def send_ping(self):
        """Send ping to keep connection alive."""
        if not self.connected or not self.websocket:
            return
        
        try:
            import time
            message = {
                "type": "ping",
                "timestamp": time.time()
            }
            await self.websocket.send(json.dumps(message))
        
        except Exception as e:
            logger.error(f"Error sending ping: {e}")
    
    async def disconnect(self):
        """Disconnect from server."""
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("Disconnected from server")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
        
        self.connected = False
        self.websocket = None
    
    async def run(self, command_executor):
        """
        Run client main loop.
        
        Args:
            command_executor: CommandExecutor instance
        """
        if not await self.connect():
            return
        
        try:
            while self.connected:
                message = await self.receive_message()
                
                if message is None:
                    break
                
                msg_type = message.get("type")
                
                if msg_type == "command_queued":
                    logger.info(f"Command queued: {message.get('message')}")
                
                elif msg_type == "error":
                    logger.error(f"Server error: {message.get('message')}")
                
                elif msg_type == "pong":
                    logger.debug("Pong received")
        
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        
        finally:
            await self.disconnect()
