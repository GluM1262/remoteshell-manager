"""
Configuration manager for client settings.
Loads configuration from YAML file.
"""

import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Server connection configuration."""
    url: str = "ws://localhost:8000/ws"
    token: str = ""
    use_ssl: bool = False
    reconnect_interval: int = 10
    ping_interval: int = 30


@dataclass
class SecurityConfig:
    """Security configuration."""
    validate_ssl: bool = True
    enable_whitelist: bool = False
    allowed_commands: List[str] = field(default_factory=list)
    blocked_commands: List[str] = field(default_factory=list)
    max_execution_time: int = 30
    max_command_length: int = 1000
    allow_shell_operators: bool = False


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
    max_size: int = 10485760  # 10MB
    console: bool = True
    backup_count: int = 5


@dataclass
class ClientConfig:
    """Complete client configuration."""
    server: ServerConfig = field(default_factory=ServerConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class ConfigManager:
    """
    Manages client configuration from YAML file.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config: Optional[ClientConfig] = None
        logger.info(f"Config manager initialized with {config_path}")
    
    def load(self) -> ClientConfig:
        """
        Load configuration from YAML file.
        
        Returns:
            ClientConfig instance
        """
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            logger.info("Using default configuration")
            self.config = ClientConfig()
            return self.config
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning("Empty config file, using defaults")
                self.config = ClientConfig()
                return self.config
            
            # Parse configuration sections
            server_data = data.get('server', {})
            security_data = data.get('security', {})
            logging_data = data.get('logging', {})
            
            self.config = ClientConfig(
                server=ServerConfig(
                    url=server_data.get('url', 'ws://localhost:8000/ws'),
                    token=server_data.get('token', ''),
                    use_ssl=server_data.get('use_ssl', False),
                    reconnect_interval=server_data.get('reconnect_interval', 10),
                    ping_interval=server_data.get('ping_interval', 30)
                ),
                security=SecurityConfig(
                    validate_ssl=security_data.get('validate_ssl', True),
                    enable_whitelist=security_data.get('enable_whitelist', False),
                    allowed_commands=security_data.get('allowed_commands', []),
                    blocked_commands=security_data.get('blocked_commands', []),
                    max_execution_time=security_data.get('max_execution_time', 30),
                    max_command_length=security_data.get('max_command_length', 1000),
                    allow_shell_operators=security_data.get('allow_shell_operators', False)
                ),
                logging=LoggingConfig(
                    level=logging_data.get('level', 'INFO'),
                    file=logging_data.get('file'),
                    max_size=logging_data.get('max_size', 10485760),
                    backup_count=logging_data.get('backup_count', 5)
                )
            )
            
            logger.info("Configuration loaded successfully")
            logger.info(f"Server URL: {self.config.server.url}")
            logger.info(f"Security whitelist: {self.config.security.enable_whitelist}")
            
            return self.config
        
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default configuration")
            self.config = ClientConfig()
            return self.config
    
    def save(self, config: ClientConfig) -> bool:
        """
        Save configuration to YAML file.
        
        Args:
            config: Configuration to save
            
        Returns:
            True if successful
        """
        try:
            data = {
                'server': {
                    'url': config.server.url,
                    'token': config.server.token,
                    'use_ssl': config.server.use_ssl,
                    'reconnect_interval': config.server.reconnect_interval,
                    'ping_interval': config.server.ping_interval
                },
                'security': {
                    'validate_ssl': config.security.validate_ssl,
                    'enable_whitelist': config.security.enable_whitelist,
                    'allowed_commands': config.security.allowed_commands,
                    'blocked_commands': config.security.blocked_commands,
                    'max_execution_time': config.security.max_execution_time,
                    'max_command_length': config.security.max_command_length,
                    'allow_shell_operators': config.security.allow_shell_operators
                },
                'logging': {
                    'level': config.logging.level,
                    'file': config.logging.file,
                    'max_size': config.logging.max_size,
                    'backup_count': config.logging.backup_count
                }
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self) -> ClientConfig:
        """
        Get current configuration.
        
        Returns:
            ClientConfig instance
        """
        if self.config is None:
            return self.load()
        return self.config
