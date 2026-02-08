"""Client entry point for RemoteShell Manager.

This module provides a CLI interface for connecting to the RemoteShell Manager
server and executing commands interactively.
"""

import argparse
import asyncio
import logging
import sys
from typing import Optional

from websocket_client import WebSocketClient

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
        print("\n👋 Goodbye!")
        sys.exit(0)
