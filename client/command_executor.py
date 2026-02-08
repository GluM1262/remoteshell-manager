"""
Command executor with security validation and timeout enforcement.
"""

import asyncio
import subprocess
import time
from typing import Dict, Optional, Set
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Executes shell commands safely with security controls."""
    
    # Dangerous shell operators
    SHELL_OPERATORS = [';', '&&', '||', '|', '>', '>>', '<', '`', '$(']
    
    def __init__(self, config):
        """
        Initialize command executor.
        
        Args:
            config: Configuration object with security settings
        """
        self.config = config
        
        # Load whitelist/blacklist
        security_config = getattr(config, 'security', None)
        if security_config:
            self.whitelist_enabled = getattr(security_config, 'enable_whitelist', False)
            self.allowed_commands = set(getattr(security_config, 'allowed_commands', []))
            self.blocked_commands = set(getattr(security_config, 'blocked_commands', []))
            self.max_execution_time = getattr(security_config, 'max_execution_time', 30)
            self.max_command_length = getattr(security_config, 'max_command_length', 1000)
            self.allow_shell_operators = getattr(security_config, 'allow_shell_operators', False)
        else:
            self.whitelist_enabled = False
            self.allowed_commands = set()
            self.blocked_commands = set()
            self.max_execution_time = 30
            self.max_command_length = 1000
            self.allow_shell_operators = False
        
        logger.info(f"Command executor initialized: whitelist={self.whitelist_enabled}")
    
    async def execute(self, command: str, timeout: Optional[int] = None) -> Dict:
        """
        Execute command with security validation.
        
        Args:
            command: Command to execute
            timeout: Optional timeout override
            
        Returns:
            Dict with stdout, stderr, exit_code, execution_time
        """
        start_time = time.time()
        
        # Check command length
        if len(command) > self.max_command_length:
            logger.warning(f"Command exceeds maximum length: {len(command)}")
            return {
                "stdout": "",
                "stderr": f"Command exceeds maximum length ({self.max_command_length})",
                "exit_code": -1,
                "execution_time": 0.0
            }
        
        # Enforce maximum execution time
        if timeout is None:
            timeout = self.max_execution_time
        else:
            timeout = min(timeout, self.max_execution_time)
        
        # Security validation
        if not self._is_command_allowed(command):
            logger.warning(f"Blocked command: {command}")
            return {
                "stdout": "",
                "stderr": "Command blocked by security policy",
                "exit_code": -1,
                "execution_time": 0.0
            }
        
        # Check shell operators
        if not self.allow_shell_operators:
            if self._contains_shell_operators(command):
                logger.warning(f"Blocked command with shell operators: {command}")
                return {
                    "stdout": "",
                    "stderr": "Command contains disallowed shell operators",
                    "exit_code": -1,
                    "execution_time": 0.0
                }
        
        # Execute with enforced timeout
        try:
            logger.info(f"Executing command: {command} (timeout: {timeout}s)")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                execution_time = time.time() - start_time
                
                return {
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                    "exit_code": process.returncode,
                    "execution_time": execution_time
                }
            
            except asyncio.TimeoutError:
                # Kill the process
                process.kill()
                await process.wait()
                
                execution_time = time.time() - start_time
                logger.warning(f"Command timed out after {timeout}s: {command}")
                
                return {
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds",
                    "exit_code": -1,
                    "execution_time": execution_time
                }
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing command: {e}")
            return {
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "exit_code": -1,
                "execution_time": execution_time
            }
    
    def _is_command_allowed(self, command: str) -> bool:
        """
        Validate command against whitelist/blacklist.
        
        Args:
            command: Command to validate
            
        Returns:
            True if command is allowed, False otherwise
        """
        command_stripped = command.strip()
        
        # Check blacklist first (always enforced)
        for blocked in self.blocked_commands:
            if blocked.lower() in command.lower():
                return False
        
        # Check whitelist (if enabled)
        if self.whitelist_enabled:
            base_command = command_stripped.split()[0] if command_stripped else ""
            
            # Must match whitelist
            if base_command not in self.allowed_commands:
                # Check if command starts with any allowed command
                allowed = any(
                    command_stripped.startswith(cmd) 
                    for cmd in self.allowed_commands
                )
                return allowed
        
        return True
    
    def _contains_shell_operators(self, command: str) -> bool:
        """
        Check if command contains shell operators.
        
        Args:
            command: Command to check
            
        Returns:
            True if command contains shell operators
        """
        for operator in self.SHELL_OPERATORS:
            if operator in command:
                return True
        return False
