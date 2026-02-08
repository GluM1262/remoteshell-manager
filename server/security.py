"""
Security manager for RemoteShell server.
Handles command validation, whitelisting, and security policies.
"""

import re
from typing import List, Optional, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SecurityPolicy:
    """Security policy configuration."""
    enable_whitelist: bool = False
    allowed_commands: List[str] = None
    blocked_commands: List[str] = None
    max_execution_time: int = 30
    max_command_length: int = 1000
    allow_shell_operators: bool = False
    
    def __post_init__(self):
        if self.allowed_commands is None:
            self.allowed_commands = []
        if self.blocked_commands is None:
            self.blocked_commands = []

class SecurityManager:
    """
    Manages security policies and command validation.
    """
    
    # Default blocked commands (always enforced)
    DEFAULT_BLOCKED_COMMANDS = [
        "rm -rf /",
        "mkfs",
        "dd if=/dev/zero",
        ":(){ :|:& };:",  # Fork bomb
        "chmod -R 777 /",
        "chown -R",
        "> /dev/sda",
        "mv / /dev/null",
    ]
    
    # Default safe commands (for whitelist mode)
    DEFAULT_SAFE_COMMANDS = [
        "ls", "pwd", "whoami", "hostname", "uptime",
        "df", "du", "free", "ps", "top",
        "cat", "grep", "find", "echo",
        "date", "uname", "which", "whereis",
        "netstat", "ss", "ip", "ifconfig",
        "systemctl status", "journalctl",
    ]
    
    # Dangerous shell operators
    SHELL_OPERATORS = [";", "&&", "||", "|", ">", ">>", "<", "$(", "`"]
    
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        self._whitelist_cache: Optional[Set[str]] = None
        self._blacklist_cache: Optional[Set[str]] = None
        
        logger.info(f"Security manager initialized: whitelist={policy.enable_whitelist}")
    
    def validate_command(self, command: str, device_id: str = None) -> tuple[bool, Optional[str]]:
        """
        Validate command against security policy.
        
        Args:
            command: Command to validate
            device_id: Device requesting command execution
            
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if command is allowed
            - (False, error_message) if command is blocked
        """
        # Check command length
        if len(command) > self.policy.max_command_length:
            return False, f"Command exceeds maximum length ({self.policy.max_command_length})"
        
        # Check for empty command
        if not command.strip():
            return False, "Empty command"
        
        # Check blacklist (always enforced)
        if self._is_blacklisted(command):
            logger.warning(f"Blocked dangerous command from {device_id}: {command}")
            return False, "Command blocked by security policy (dangerous operation)"
        
        # Check shell operators
        if not self.policy.allow_shell_operators:
            if self._contains_shell_operators(command):
                logger.warning(f"Blocked command with shell operators from {device_id}: {command}")
                return False, "Command contains disallowed shell operators"
        
        # Check whitelist (if enabled)
        if self.policy.enable_whitelist:
            if not self._is_whitelisted(command):
                logger.warning(f"Command not in whitelist from {device_id}: {command}")
                return False, "Command not in allowed whitelist"
        
        return True, None
    
    def _is_blacklisted(self, command: str) -> bool:
        """Check if command matches blacklist."""
        if self._blacklist_cache is None:
            self._blacklist_cache = set(
                self.DEFAULT_BLOCKED_COMMANDS + self.policy.blocked_commands
            )
        
        command_lower = command.lower().strip()
        
        for blocked in self._blacklist_cache:
            if blocked.lower() in command_lower:
                return True
        
        return False
    
    def _is_whitelisted(self, command: str) -> bool:
        """Check if command matches whitelist."""
        if not self.policy.enable_whitelist:
            return True
        
        if self._whitelist_cache is None:
            whitelist = self.policy.allowed_commands or self.DEFAULT_SAFE_COMMANDS
            self._whitelist_cache = set(whitelist)
        
        # Extract base command (first word)
        base_command = command.strip().split()[0]
        
        # Check exact matches
        if base_command in self._whitelist_cache:
            return True
        
        # Check if any whitelist entry is a prefix
        for allowed in self._whitelist_cache:
            if command.strip().startswith(allowed):
                return True
        
        return False
    
    def _contains_shell_operators(self, command: str) -> bool:
        """Check if command contains shell operators."""
        for operator in self.SHELL_OPERATORS:
            if operator in command:
                return True
        return False
    
    def get_max_execution_time(self, requested_timeout: Optional[int] = None) -> int:
        """
        Get effective execution timeout.
        
        Args:
            requested_timeout: Timeout requested by client
            
        Returns:
            Effective timeout (minimum of requested and policy max)
        """
        if requested_timeout is None:
            return self.policy.max_execution_time
        
        return min(requested_timeout, self.policy.max_execution_time)
