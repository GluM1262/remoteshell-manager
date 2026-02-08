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
