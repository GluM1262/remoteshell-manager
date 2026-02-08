"""Configuration settings for RemoteShell Manager."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
