"""
Configuration manager for RemoteShell client.
Handles loading and validating configuration from YAML file.
"""

import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class ServerConfig:
    """Server connection configuration."""
    host: str
    port: int
    use_ssl: bool = False
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 0
    ping_interval: int = 30
    ping_timeout: int = 10

@dataclass
class DeviceConfig:
    """Device authentication configuration."""
    device_id: str
    token: str

@dataclass
class ExecutionConfig:
    """Command execution configuration."""
    timeout: int = 30
    shell: str = "/bin/bash"
    working_directory: str = "~"
    capture_output: bool = True

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file: Optional[str] = "client.log"
    console: bool = True
    max_size: int = 10485760
    backup_count: int = 5

@dataclass
class SecurityConfig:
    """Security configuration."""
    validate_ssl: bool = True
    allowed_commands: Optional[list] = None
    blocked_commands: Optional[list] = None

class ConfigManager:
    """Manages client configuration."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.server: Optional[ServerConfig] = None
        self.device: Optional[DeviceConfig] = None
        self.execution: Optional[ExecutionConfig] = None
        self.logging: Optional[LoggingConfig] = None
        self.security: Optional[SecurityConfig] = None
        
    def load(self) -> bool:
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Parse server config
            server_data = config_data.get('server', {})
            self.server = ServerConfig(**server_data)
            
            # Parse device config
            device_data = config_data.get('device', {})
            self.device = DeviceConfig(**device_data)
            
            # Parse execution config
            execution_data = config_data.get('execution', {})
            self.execution = ExecutionConfig(**execution_data)
            
            # Parse logging config
            logging_data = config_data.get('logging', {})
            self.logging = LoggingConfig(**logging_data)
            
            # Parse security config
            security_data = config_data.get('security', {})
            self.security = SecurityConfig(**security_data)
            
            self.validate()
            return True
            
        except Exception as e:
            print(f"Failed to load config: {e}")
            return False
    
    def validate(self):
        """Validate configuration values."""
        if not self.device.device_id:
            raise ValueError("device_id is required")
        if not self.device.token:
            raise ValueError("device token is required")
        if not self.server.host:
            raise ValueError("server host is required")
    
    def get_websocket_url(self) -> str:
        """Build WebSocket URL with authentication token."""
        protocol = "wss" if self.server.use_ssl else "ws"
        url = f"{protocol}://{self.server.host}:{self.server.port}/ws"
        url += f"?token={self.device.token}"
        return url
