"""
Server configuration with security and TLS settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server configuration settings."""
"""Configuration settings for RemoteShell Manager."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
"""
Configuration Management Module

Handles server configuration using pydantic-settings.
Loads settings from environment variables and .env file.
"""

from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    # TLS/SSL Settings
    use_tls: bool = False
    tls_cert_path: Optional[str] = "tls/cert.pem"
    tls_key_path: Optional[str] = "tls/key.pem"
    tls_ca_path: Optional[str] = None
    
    # Authentication
    device_tokens: Optional[str] = None  # Comma-separated list of tokens
    
    # Security Settings
    enable_command_whitelist: bool = False
    allowed_commands: List[str] = [
        "ls", "pwd", "whoami", "hostname", "uptime",
        "df", "du", "free", "ps", "top",
        "cat", "grep", "find", "echo", "date"
    ]
    blocked_commands: List[str] = []
    max_execution_time: int = 30
    max_command_length: int = 1000
    allow_shell_operators: bool = False
    
    # User execution (for documentation)
    run_as_user: str = "remoteshell"
    run_as_group: str = "remoteshell"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    debug: bool = False
    log_level: str = "INFO"
    
    # Security
    secret_key: str = "change-me-in-production"
    token_expiration: int = 3600  # seconds
    
    # Database
    database_path: str = "remoteshell.db"
    database_pool_size: int = 5
    history_retention_days: int = 30
    
    # Queue
    max_queue_size: int = 100
    queue_timeout: int = 300  # 5 minutes
    command_default_timeout: int = 30  # seconds
    
    # WebSocket
    websocket_timeout: int = 60  # seconds
    websocket_ping_interval: int = 30  # seconds
    
    # CORS
    cors_origins: list[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]
    
    # Security - Device tokens in format: "device_id:token,device_id:token"
    device_tokens: str = ""
    
    # Command execution
    command_timeout: int = 30
    max_command_length: int = 1000
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_token_dict(self) -> Dict[str, str]:
        """
        Parse device_tokens string into a dictionary.
        
        Format: "device1:token1,device2:token2"
        Returns: {"token1": "device1", "token2": "device2"}
        """
        token_dict = {}
        if self.device_tokens:
            pairs = self.device_tokens.split(",")
            for pair in pairs:
                if ":" in pair:
                    device_id, token = pair.strip().split(":", 1)
                    token_dict[token.strip()] = device_id.strip()
        return token_dict


# Global settings instance
settings = Settings()
