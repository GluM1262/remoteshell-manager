#!/usr/bin/env python3
"""
Example client script demonstrating RemoteShell Manager usage.
"""

import asyncio
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class ServerConfig:
    """Server configuration."""
    url: str = "ws://localhost:8000/ws"
    token: str = "example-token-12345678"
    use_ssl: bool = False

@dataclass  
class SecurityConfig:
    """Security configuration."""
    validate_ssl: bool = True
    enable_whitelist: bool = False
    allowed_commands: list = None
    blocked_commands: list = None
    max_execution_time: int = 30
    max_command_length: int = 1000
    allow_shell_operators: bool = False
    
    def __post_init__(self):
        if self.allowed_commands is None:
            self.allowed_commands = ["ls", "pwd", "whoami", "hostname"]
        if self.blocked_commands is None:
            self.blocked_commands = ["rm -rf /", "mkfs"]

@dataclass
class Config:
    """Configuration object."""
    server: ServerConfig
    security: SecurityConfig

async def main():
    """Main example function."""
    print("=" * 60)
    print("RemoteShell Manager - Example Client")
    print("=" * 60)
    
    # Create configuration
    config = Config(
        server=ServerConfig(
            url="ws://localhost:8000/ws",
            token="example-device-token",
            use_ssl=False
        ),
        security=SecurityConfig(
            enable_whitelist=False,
            max_execution_time=30,
            allow_shell_operators=False
        )
    )
    
    print("\n📋 Configuration:")
    print(f"  Server URL: {config.server.url}")
    print(f"  TLS Enabled: {config.server.use_ssl}")
    print(f"  Whitelist Enabled: {config.security.enable_whitelist}")
    print(f"  Max Execution Time: {config.security.max_execution_time}s")
    print(f"  Shell Operators: {config.security.allow_shell_operators}")
    
    print("\n" + "=" * 60)
    print("To run the actual client:")
    print("=" * 60)
    print("\n1. Start the server:")
    print("   cd server && python main.py")
    print("\n2. Configure the client:")
    print("   cd client")
    print("   cp config.yaml.example config.yaml")
    print("   # Edit config.yaml with your settings")
    print("\n3. Run the client:")
    print("   python websocket_client.py")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
