"""
RemoteShell Manager Client - Main entry point.
Connects to server and executes commands from devices.
"""

import asyncio
import logging
import signal
import sys
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler

from config_manager import ConfigManager
from websocket_client import WebSocketClient
from command_executor import CommandExecutor


# Global flag for graceful shutdown
shutdown_flag = False


def setup_logging(config):
    """
    Setup logging configuration.
    
    Args:
        config: Logging configuration
    """
    # Set log level
    log_level = getattr(logging, config.level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # File handler (if configured)
    if config.file:
        try:
            log_path = Path(config.file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                config.file,
                maxBytes=config.max_size,
                backupCount=config.backup_count
            )
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def signal_handler(signum, frame):
    """
    Handle shutdown signals.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    global shutdown_flag
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, initiating shutdown...")
    shutdown_flag = True


async def main_loop(client, executor, config):
    """
    Main client loop with reconnection logic.
    
    Args:
        client: WebSocket client
        executor: Command executor
        config: Client configuration
    """
    global shutdown_flag
    logger = logging.getLogger(__name__)
    
    reconnect_interval = config.server.reconnect_interval
    ping_interval = config.server.ping_interval
    
    while not shutdown_flag:
        try:
            # Connect to server
            if await client.connect():
                logger.info("Connected to server, starting main loop")
                
                # Create ping task
                async def ping_loop():
                    while not shutdown_flag and client.connected:
                        await asyncio.sleep(ping_interval)
                        if client.connected:
                            await client.send_ping()
                
                ping_task = asyncio.create_task(ping_loop())
                
                try:
                    # Handle messages from server
                    while not shutdown_flag and client.connected:
                        message = await asyncio.wait_for(
                            client.receive_message(),
                            timeout=1.0
                        )
                        
                        if message is None:
                            logger.warning("Connection lost")
                            break
                        
                        msg_type = message.get("type")
                        
                        if msg_type == "command":
                            # Execute command
                            command = message.get("command", "")
                            timeout = message.get("timeout")
                            
                            logger.info(f"Executing command: {command}")
                            result = await executor.execute(command, timeout)
                            
                            # Send result back to server
                            result_msg = {
                                "type": "command_result",
                                "command": command,
                                "stdout": result["stdout"],
                                "stderr": result["stderr"],
                                "exit_code": result["exit_code"],
                                "execution_time": result["execution_time"]
                            }
                            await client.websocket.send(json.dumps(result_msg))
                            
                            logger.info(f"Command completed with exit code {result['exit_code']}")
                        
                        elif msg_type == "pong":
                            logger.debug("Pong received")
                        
                        elif msg_type == "connected":
                            logger.info(f"Server welcome: {message.get('message')}")
                        
                        elif msg_type == "error":
                            logger.error(f"Server error: {message.get('message')}")
                
                except asyncio.TimeoutError:
                    # Normal timeout, continue loop
                    pass
                except Exception as e:
                    logger.error(f"Error in message loop: {e}")
                finally:
                    ping_task.cancel()
                    await client.disconnect()
            else:
                logger.error("Failed to connect to server")
        
        except Exception as e:
            logger.error(f"Connection error: {e}")
        
        # Reconnect if not shutting down
        if not shutdown_flag:
            logger.info(f"Reconnecting in {reconnect_interval} seconds...")
            await asyncio.sleep(reconnect_interval)
    
    logger.info("Client shutting down")


async def main():
    """Main entry point."""
    global shutdown_flag
    
    # Load configuration
    config_mgr = ConfigManager("config.yaml")
    config = config_mgr.load()
    
    # Setup logging
    setup_logging(config.logging)
    
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("RemoteShell Manager Client Starting")
    logger.info("="*60)
    logger.info(f"Server: {config.server.url}")
    logger.info(f"Security whitelist: {config.security.enable_whitelist}")
    logger.info(f"Max execution time: {config.security.max_execution_time}s")
    logger.info("="*60)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create client and executor
    client = WebSocketClient(config)
    executor = CommandExecutor(config)
    
    try:
        # Run main loop
        await main_loop(client, executor, config)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await client.disconnect()
        logger.info("Client stopped")
