#!/usr/bin/env python3
"""
RemoteShell Client - Linux device client for remote command execution.

Usage:
    python main.py [--config CONFIG_PATH]
"""

import asyncio
import signal
import sys
import argparse
from pathlib import Path

from config_manager import ConfigManager
from logger import setup_logger
from command_executor import CommandExecutor
from websocket_client import WebSocketClient

class RemoteShellClient:
    """Main client application."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.logger = None
        self.executor = None
        self.ws_client = None
        
    def initialize(self) -> bool:
        """Initialize client components."""
        # Load configuration
        if not self.config_manager.load():
            print("Failed to load configuration")
            return False
        
        # Setup logger
        self.logger = setup_logger(self.config_manager.logging)
        self.logger.info("=== RemoteShell Client Starting ===")
        self.logger.info(f"Device ID: {self.config_manager.device.device_id}")
        self.logger.info(f"Server: {self.config_manager.server.host}:{self.config_manager.server.port}")
        
        # Create executor
        self.executor = CommandExecutor(self.config_manager, self.logger)
        
        # Create WebSocket client
        self.ws_client = WebSocketClient(self.config_manager, self.executor, self.logger)
        
        return True
    
    async def run(self):
        """Run the client."""
        try:
            await self.ws_client.start()
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Client error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown client gracefully."""
        self.logger.info("Shutting down...")
        if self.ws_client:
            await self.ws_client.stop()
        self.logger.info("Client stopped")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="RemoteShell Client")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    args = parser.parse_args()
    
    # Create and initialize client
    client = RemoteShellClient(args.config)
    if not client.initialize():
        sys.exit(1)
    
    # Setup signal handlers
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(client.shutdown()))
    
    # Run client
    try:
        loop.run_until_complete(client.run())
    finally:
        loop.close()

if __name__ == "__main__":
    main()
