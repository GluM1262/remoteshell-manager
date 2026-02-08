"""
Server configuration with security and TLS settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server configuration settings."""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    # TLS/SSL Settings
    use_tls: bool = False
    tls_cert_path: Optional[str] = "tls/cert.pem"
    tls_key_path: Optional[str] = "tls/key.pem"
    tls_ca_path: Optional[str] = None
    
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
