"""
Shell Command Executor

Executes shell commands asynchronously with timeout and security validation.
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
