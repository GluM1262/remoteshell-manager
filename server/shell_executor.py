"""Shell command executor for RemoteShell Manager.

This module provides safe asynchronous execution of shell commands
with timeout handling and output capture.
"""

import asyncio
import logging
import time
import shlex
from typing import Dict

logger = logging.getLogger(__name__)

# Blacklist of dangerous commands (basic security)
DANGEROUS_COMMANDS = [
    "rm -rf /",
    ":(){ :|:& };:",  # Fork bomb
    "mkfs",
    "dd if=/dev/zero",
    "mv / ",
    "chmod -R 777 /",
]


def is_command_safe(command: str) -> bool:
    """
    Basic validation to check if command is potentially dangerous.
    
    SECURITY NOTE: This is a blacklist approach which is not foolproof.
    For production environments with untrusted input, strongly consider:
    - Implementing a whitelist of allowed commands
    - Using more sophisticated sandboxing (e.g., containers, chroot)
    - Restricting shell features (disable pipes, redirects, etc.)
    
    Args:
        command: Command string to validate
        
    Returns:
        True if command appears safe, False otherwise
    """
    command_lower = command.lower().strip()
    
    # Check against blacklist
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous.lower() in command_lower:
            logger.warning(f"Blocked dangerous command: {command}")
            return False
    
    # Additional checks can be added here
    # For production, consider implementing a whitelist instead
    
    return True


async def execute_command(command: str, timeout: int = 30) -> Dict:
    """
    Execute shell command asynchronously and return results.
    
    Args:
        command: Shell command to execute
        timeout: Maximum execution time in seconds
        
    Returns:
        Dictionary containing:
            - stdout: Standard output string
            - stderr: Standard error string
            - exit_code: Command exit code
            - execution_time: Time taken to execute in seconds
            
    Raises:
        asyncio.TimeoutError: If command execution exceeds timeout
        ValueError: If command is deemed unsafe
    """
    # Security validation
    if not is_command_safe(command):
        raise ValueError(f"Command blocked for security reasons: {command}")
    
    if len(command) > 10000:
        raise ValueError("Command too long")
    
    logger.info(f"Executing command: {command[:100]}...")
    start_time = time.time()
    
    try:
        # Note: Using shell=True allows complex commands with pipes, redirects, etc.
        # This is necessary for flexibility but requires careful input validation.
        # The is_command_safe() function provides basic protection.
        # For production environments with untrusted input, consider:
        # 1. Using a command whitelist approach
        # 2. Restricting to specific command patterns
        # 3. Using shell=False with shlex.split() for simpler commands
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        
        # Wait for command to complete with timeout
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        stdout = stdout_bytes.decode('utf-8', errors='replace')
        stderr = stderr_bytes.decode('utf-8', errors='replace')
        exit_code = process.returncode
        
    except asyncio.TimeoutError:
        logger.error(f"Command timed out after {timeout}s: {command}")
        # Try to kill the process
        try:
            process.kill()
            await process.wait()
        except Exception as e:
            logger.error(f"Failed to kill timed-out process: {e}")
        
        raise asyncio.TimeoutError(f"Command execution timed out after {timeout} seconds")
    
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        execution_time = time.time() - start_time
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "execution_time": execution_time
        }
    
    execution_time = time.time() - start_time
    
    logger.info(f"Command completed in {execution_time:.2f}s with exit code {exit_code}")
    
    return {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "execution_time": execution_time
    }
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
