"""
Authentication module for device token validation.
"""

import os
import logging
from typing import Optional, Set
import secrets
Authentication Module

Handles device token authentication using secure comparison.
"""

import hmac
import logging
from typing import Optional
from server.config import settings

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Manages device authentication using tokens.
    Tokens can be loaded from environment variables or files.
    """
    
    def __init__(self, tokens: Optional[Set[str]] = None):
        """
        Initialize authentication manager.
        
        Args:
            tokens: Set of valid device tokens
        """
        self.valid_tokens: Set[str] = tokens or set()
        self._load_tokens_from_env()
        logger.info(f"Auth manager initialized with {len(self.valid_tokens)} tokens")
    
    def _load_tokens_from_env(self):
        """Load device tokens from DEVICE_TOKENS environment variable."""
        device_tokens = os.getenv("DEVICE_TOKENS", "")
        
        if device_tokens:
            # Tokens can be comma-separated
            tokens = [t.strip() for t in device_tokens.split(",") if t.strip()]
            self.valid_tokens.update(tokens)
            logger.info(f"Loaded {len(tokens)} tokens from environment")
    
    def validate_token(self, token: str) -> bool:
        """
        Validate device authentication token.
        
        Args:
            token: Token to validate
            
        Returns:
            True if token is valid
        """
        if not token:
            return False
        
        is_valid = token in self.valid_tokens
        
        if not is_valid:
            logger.warning(f"Invalid token attempt: {token[:8]}...")
        
        return is_valid
    
    def add_token(self, token: str) -> bool:
        """
        Add a new valid token.
        
        Args:
            token: Token to add
            
        Returns:
            True if added (False if already exists)
        """
        if token in self.valid_tokens:
            return False
        
        self.valid_tokens.add(token)
        logger.info(f"New token added: {token[:8]}...")
        return True
    
    def remove_token(self, token: str) -> bool:
        """
        Remove a token.
        
        Args:
            token: Token to remove
            
        Returns:
            True if removed (False if didn't exist)
        """
        if token not in self.valid_tokens:
            return False
        
        self.valid_tokens.remove(token)
        logger.info(f"Token removed: {token[:8]}...")
        return True
    
    def generate_token(self, length: int = 32) -> str:
        """
        Generate a new secure random token.
        
        Args:
            length: Token length in characters
            
        Returns:
            Generated token
        """
        token = secrets.token_urlsafe(length)
        logger.info(f"Generated new token: {token[:8]}...")
        return token
    
    def list_tokens(self) -> list[str]:
        """
        Get list of all valid tokens (first 8 chars only for security).
        
        Returns:
            List of token prefixes
        """
        return [f"{token[:8]}..." for token in self.valid_tokens]
    
    def get_device_id_from_token(self, token: str) -> str:
        """
        Generate device ID from token.
        
        Args:
            token: Authentication token
            
        Returns:
            Device identifier
        """
        # Use first 12 chars of token as device ID
        return f"device_{token[:12]}"
def validate_token(token: str) -> bool:
    """
    Validate device token using constant-time comparison.
    
    Args:
        token: Device token to validate
        
    Returns:
        True if token is valid, False otherwise
    """
    if not token:
        return False
    
    token_dict = settings.get_token_dict()
    
    # Use constant-time comparison to prevent timing attacks
    for valid_token in token_dict.keys():
        if hmac.compare_digest(token, valid_token):
            return True
    
    return False


def get_device_id(token: str) -> Optional[str]:
    """
    Get device identifier from token.
    
    Args:
        token: Valid device token
        
    Returns:
        Device ID if token is valid, None otherwise
    """
    if not token:
        return None
    
    token_dict = settings.get_token_dict()
    
    # Use constant-time comparison
    for valid_token, device_id in token_dict.items():
        if hmac.compare_digest(token, valid_token):
            return device_id
    
    return None


def load_tokens_info() -> dict:
    """
    Load and return information about configured tokens.
    
    Returns:
        Dictionary with token count and device IDs
    """
    token_dict = settings.get_token_dict()
    return {
        "token_count": len(token_dict),
        "device_ids": list(token_dict.values())
    }
