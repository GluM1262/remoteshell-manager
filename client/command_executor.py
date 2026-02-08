"""
Command execution handler for RemoteShell client.
Handles async subprocess execution with timeout and security validation.
"""

import asyncio
from typing import Dict, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Executes shell commands with security validation."""
    
    def __init__(self, security_config, execution_config):
        self.security = security_config
        self.execution = execution_config
    
    def validate_command(self, command: str) -> tuple[bool, Optional[str]]:
        """Validate command against security policy."""
        # Check blocked commands
        for blocked in self.security.blocked_commands:
            if blocked in command:
                return False, f"Command contains blocked pattern: {blocked}"
        
        # Check allowed commands (if whitelist is configured)
        if self.security.allowed_commands:
            allowed = any(command.startswith(cmd) for cmd in self.security.allowed_commands)
            if not allowed:
                return False, "Command not in allowed whitelist"
        
        return True, None
    
    async def execute(self, command: str, timeout: Optional[int] = None) -> Dict:
        """Execute shell command and return results."""
        start_time = datetime.now(timezone.utc)
        
        # Validate command
        is_valid, error = self.validate_command(command)
        if not is_valid:
            logger.warning(f"Command validation failed: {error}")
            return {
                "stdout": "",
                "stderr": error,
                "exit_code": -1,
                "execution_time": 0.0,
                "timestamp": start_time.isoformat()
            }
        
        # Use provided timeout or default
        exec_timeout = timeout or self.execution.timeout
        
        try:
            # Create subprocess
            # NOTE: Using shell=True allows for shell features (pipes, redirection, etc.)
            # but requires careful security validation via whitelist/blacklist to prevent
            # command injection. All commands are validated before execution.
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=exec_timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Command timed out after {exec_timeout} seconds")
            
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            return {
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "exit_code": process.returncode,
                "execution_time": execution_time,
                "timestamp": start_time.isoformat()
            }
            
        except TimeoutError as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"Command timeout: {command}")
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "execution_time": execution_time,
                "timestamp": start_time.isoformat()
            }
        except Exception as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"Command execution error: {e}")
            return {
                "stdout": "",
                "stderr": f"Execution error: {str(e)}",
                "exit_code": -1,
                "execution_time": execution_time,
                "timestamp": start_time.isoformat()
            }
