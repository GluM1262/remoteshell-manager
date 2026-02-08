"""
Configuration manager for RemoteShell client.
Handles loading and validating configuration from YAML file.
"""

import yaml
from typing import Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class ServerConfig:
    """Server connection configuration."""
    host: str = "localhost"
    port: int = 8000
    use_ssl: bool = False
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 0
    ping_interval: int = 30
    ping_timeout: int = 10


@dataclass
class DeviceConfig:
    """Device authentication configuration."""
    device_id: str = ""
    token: str = ""


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
    allowed_commands: list[str] = field(default_factory=list)
    blocked_commands: list[str] = field(default_factory=lambda: [
        "rm -rf /",
        "mkfs",
        "dd if=/dev/zero"
    ])


class ConfigManager:
    """Manages client configuration."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.server = ServerConfig()
        self.device = DeviceConfig()
        self.execution = ExecutionConfig()
        self.logging = LoggingConfig()
        self.security = SecurityConfig()
        
    def load(self) -> bool:
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Parse server config
            if 'server' in config_data:
                self.server = ServerConfig(**config_data['server'])
            
            # Parse device config
            if 'device' in config_data:
                self.device = DeviceConfig(**config_data['device'])
            
            # Parse execution config
            if 'execution' in config_data:
                self.execution = ExecutionConfig(**config_data['execution'])
            
            # Parse logging config
            if 'logging' in config_data:
                self.logging = LoggingConfig(**config_data['logging'])
            
            # Parse security config
            if 'security' in config_data:
                sec_data = config_data['security']
                self.security = SecurityConfig(
                    validate_ssl=sec_data.get('validate_ssl', True),
                    allowed_commands=sec_data.get('allowed_commands', []),
                    blocked_commands=sec_data.get('blocked_commands', self.security.blocked_commands)
                )
            
            return True
        except Exception as e:
            print(f"Error loading config: {e}")
            return False
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate configuration."""
        if not self.device.device_id:
            return False, "Device ID is required"
        if not self.device.token:
            return False, "Device token is required"
        if not self.server.host:
            return False, "Server host is required"
        return True, None
