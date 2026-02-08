"""
WebSocket client for RemoteShell.
Handles connection, authentication, and message exchange with server.
"""

import asyncio
import websockets
import json
from typing import Optional, Callable
from datetime import datetime

class WebSocketClient:
    """WebSocket client for server communication."""
    
    def __init__(self, config, executor, logger):
        self.config = config
        self.executor = executor
        self.logger = logger
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.reconnect_attempts = 0
        
    async def connect(self):
        """Connect to server with authentication."""
        url = self.config.get_websocket_url()
        
        self.logger.info(f"Connecting to {url}")
        
        try:
            # Create SSL context if needed
            ssl_context = None
            if self.config.server.use_ssl:
                import ssl
                ssl_context = ssl.create_default_context()
                if not self.config.security.validate_ssl:
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect to WebSocket
            self.ws = await websockets.connect(
                url,
                ssl=ssl_context,
                ping_interval=self.config.server.ping_interval,
                ping_timeout=self.config.server.ping_timeout
            )
            
            self.logger.info("Connected to server successfully")
            self.reconnect_attempts = 0
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    async def start(self):
        """Start client and handle reconnection logic."""
        self.running = True
        
        while self.running:
            try:
                # Connect to server
                if await self.connect():
                    # Handle messages
                    await self._message_loop()
                
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("Connection closed by server")
            except Exception as e:
                self.logger.error(f"Error in client loop: {e}")
            
            # Reconnection logic
            if self.running:
                self.reconnect_attempts += 1
                max_attempts = self.config.server.max_reconnect_attempts
                
                if max_attempts > 0 and self.reconnect_attempts >= max_attempts:
                    self.logger.error(f"Max reconnection attempts ({max_attempts}) reached")
                    break
                
                interval = self.config.server.reconnect_interval
                self.logger.info(f"Reconnecting in {interval} seconds (attempt {self.reconnect_attempts})...")
                await asyncio.sleep(interval)
    
    async def _message_loop(self):
        """Main message handling loop."""
        async for message in self.ws:
            try:
                data = json.loads(message)
                await self._handle_message(data)
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON received: {message}")
            except Exception as e:
                self.logger.error(f"Error handling message: {e}")
    
    async def _handle_message(self, data: dict):
        """
        Handle incoming message from server.
        
        Args:
            data: Parsed JSON message
        """
        msg_type = data.get("type")
        
        if msg_type == "command":
            await self._handle_command(data)
        elif msg_type == "ping":
            await self._send_pong()
        else:
            self.logger.warning(f"Unknown message type: {msg_type}")
    
    async def _handle_command(self, data: dict):
        """
        Handle command execution request.
        
        Args:
            data: Command message data
        """
        command_id = data.get("id")
        command = data.get("command")
        timeout = data.get("timeout", self.config.execution.timeout)
        
        self.logger.info(f"Received command [{command_id}]: {command}")
        
        # Execute command
        result = await self.executor.execute(command, timeout)
        
        # Send response back to server
        response = {
            "type": "response",
            "id": command_id,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
            "execution_time": result["execution_time"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._send_message(response)
    
    async def _send_message(self, data: dict):
        """Send message to server."""
        if self.ws and not self.ws.closed:
            try:
                await self.ws.send(json.dumps(data))
            except Exception as e:
                self.logger.error(f"Failed to send message: {e}")
    
    async def _send_pong(self):
        """Send pong response to keep connection alive."""
        await self._send_message({"type": "pong"})
    
    async def stop(self):
        """Stop client and close connection."""
        self.running = False
        if self.ws and not self.ws.closed:
            await self.ws.close()
            self.logger.info("Connection closed")
