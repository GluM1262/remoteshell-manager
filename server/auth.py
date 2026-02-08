"""
Authentication Module

Handles device token authentication using secure comparison.
"""

import hmac
import logging
from typing import Optional
from server.config import settings

logger = logging.getLogger(__name__)


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
