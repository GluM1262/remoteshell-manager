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
"""Client entry point for RemoteShell Manager.

This module provides a CLI interface for connecting to the RemoteShell Manager
server and executing commands interactively.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.websocket_client import WebSocketClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RemoteShellClient:
    """Interactive client for RemoteShell Manager."""
    
    def __init__(self, host: str, port: int):
        """Initialize the client.
        
        Args:
            host: Server hostname or IP address
            port: Server port number
        """
        self.client = WebSocketClient(host, port)
        self.running = False
        self.command_history = []
    
    def format_response(self, response: dict) -> str:
        """Format a response for display.
        
        Args:
            response: Response dictionary from server
            
        Returns:
            Formatted string for display
        """
        msg_type = response.get("type", "unknown")
        
        if msg_type == "response":
            # Command execution response
            exit_code = response.get("exit_code", -1)
            stdout = response.get("stdout", "")
            stderr = response.get("stderr", "")
            
            output = []
            output.append(f"\n{'='*60}")
            output.append(f"Exit Code: {exit_code}")
            output.append(f"{'='*60}")
            
            if stdout:
                output.append("\n--- STDOUT ---")
                output.append(stdout.rstrip())
            
            if stderr:
                output.append("\n--- STDERR ---")
                output.append(stderr.rstrip())
            
            output.append(f"{'='*60}\n")
            return "\n".join(output)
            
        elif msg_type == "error":
            # Error message
            error = response.get("error", "Unknown error")
            return f"\n❌ ERROR: {error}\n"
            
        elif msg_type == "info":
            # Info message
            message = response.get("message", "")
            return f"\nℹ️  {message}\n"
            
        else:
            # Unknown message type
            return f"\n⚠️  Unknown response type: {msg_type}\n{response}\n"
    
    async def run_interactive(self):
        """Run the client in interactive mode."""
        self.running = True
        
        print("\n" + "="*60)
        print("RemoteShell Manager - Interactive Client")
        print("="*60)
        print(f"Connecting to {self.client.host}:{self.client.port}...")
        print("="*60 + "\n")
        
        # Connect to server
        if not await self.client.connect():
            print("❌ Failed to connect to server")
            return
        
        print("✅ Connected successfully!")
        print("\nType your commands below. Use 'exit' or 'quit' to disconnect.")
        print("Use Ctrl+C to force quit.\n")
        
        try:
            while self.running:
                try:
                    # Get command from user
                    command = await asyncio.get_event_loop().run_in_executor(
                        None,
                        input,
                        "🔹 Command: "
                    )
                    
                    # Clean command
                    command = command.strip()
                    
                    # Check for exit commands
                    if command.lower() in ["exit", "quit", "q"]:
                        print("\n👋 Disconnecting...")
                        break
                    
                    # Skip empty commands
                    if not command:
                        continue
                    
                    # Add to history
                    self.command_history.append(command)
                    
                    # Send command and get response
                    print("\n⏳ Executing command...")
                    response = await self.client.send_command(command)
                    
                    if response:
                        # Display formatted response
                        print(self.format_response(response))
                    else:
                        print("\n❌ Failed to get response from server\n")
                        
                        # Try to reconnect
                        print("Attempting to reconnect...")
                        if await self.client.auto_reconnect():
                            print("✅ Reconnected successfully!\n")
                        else:
                            print("❌ Failed to reconnect. Exiting...\n")
                            break
                    
                except EOFError:
                    # Handle Ctrl+D
                    print("\n\n👋 EOF received. Disconnecting...")
                    break
                    
        except KeyboardInterrupt:
            print("\n\n👋 Keyboard interrupt received. Disconnecting...")
        
        finally:
            await self.client.disconnect()
            self.running = False
            
            if self.command_history:
                print(f"\n📝 Commands executed in this session: {len(self.command_history)}")


async def main():
    """Main entry point for the client."""
    parser = argparse.ArgumentParser(
        description="RemoteShell Manager - Connect to remote Linux devices"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Server hostname or IP address (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port number (default: 8000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run client
    client = RemoteShellClient(args.host, args.port)
    await client.run_interactive()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nClient stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
        print("\n👋 Goodbye!")
        sys.exit(0)
