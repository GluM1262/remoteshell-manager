"""Shell command executor for RemoteShell Manager.

This module provides safe asynchronous execution of shell commands
with timeout handling and output capture.
"""

import asyncio
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class ShellExecutor:
    """Execute shell commands safely with async support."""
    
    def __init__(self, timeout: int = 30):
        """Initialize the shell executor.
        
        Args:
            timeout: Maximum time in seconds to wait for command execution
        """
        self.timeout = timeout
    
    async def execute(self, command: str) -> Tuple[str, str, int]:
        """Execute a shell command asynchronously.
        
        **SECURITY WARNING**: This method uses shell=True which allows execution
        of shell commands with full shell features (pipes, redirects, etc.).
        This is intentional for this application but creates command injection risks.
        Only use in trusted environments with validated input.
        
        Args:
            command: The shell command to execute
            
        Returns:
            Tuple containing (stdout, stderr, exit_code)
            
        Raises:
            asyncio.TimeoutError: If command execution exceeds timeout
            Exception: For other execution errors
        """
        logger.info(f"Executing command: {command[:100]}...")
        
        try:
            # Create subprocess with shell=True to support pipes, redirects, etc.
            # This is a security trade-off for functionality
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            # Wait for command to complete with timeout
            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.kill()
                await process.wait()
                logger.error(f"Command timed out after {self.timeout} seconds: {command[:100]}")
                raise
            
            # Decode output
            stdout = stdout_data.decode('utf-8', errors='replace')
            stderr = stderr_data.decode('utf-8', errors='replace')
            exit_code = process.returncode
            
            logger.info(
                f"Command completed with exit code {exit_code}. "
                f"stdout length: {len(stdout)}, stderr length: {len(stderr)}"
            )
            
            return stdout, stderr, exit_code
            
        except asyncio.TimeoutError:
            return "", f"Command execution timed out after {self.timeout} seconds", -1
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return "", f"Error executing command: {str(e)}", -1
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """Validate a command for basic security checks.
        
        **SECURITY NOTE**: This is basic validation only. For production use,
        implement comprehensive command whitelisting, sandboxing, and
        audit logging. This validation is not foolproof.
        
        Args:
            command: The command to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not command or not command.strip():
            return False, "Command cannot be empty"
        
        # Check for suspicious patterns (basic security)
        # These patterns are case-sensitive as Linux commands are case-sensitive
        dangerous_patterns = [
            "rm -rf /",
            "mkfs",
            "dd if=/dev/zero",
            "> /dev/sda",
            ":(){ :|:& };:",  # Fork bomb
        ]
        
        # Check both original and lowercase for flexibility
        for pattern in dangerous_patterns:
            if pattern in command or pattern.lower() in command.lower():
                logger.warning(f"Blocked dangerous command pattern: {pattern}")
                return False, f"Command contains dangerous pattern: {pattern}"
        
        return True, ""
