"""
Command executor for RemoteShell client.
Handles secure execution of shell commands.
"""

import asyncio
import time
from typing import Dict, Optional
import shlex
import os

class CommandExecutor:
    """Executes shell commands safely and returns results."""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
    async def execute(self, command: str, timeout: Optional[int] = None) -> Dict:
        """
        Execute shell command and return results.
        
        Args:
            command: Shell command to execute
            timeout: Execution timeout in seconds (uses config default if None)
            
        Returns:
            Dict with stdout, stderr, exit_code, and execution_time
        """
        if timeout is None:
            timeout = self.config.execution.timeout
        
        # Security check
        if not self._is_command_allowed(command):
            self.logger.warning(f"Blocked command: {command}")
            return {
                "stdout": "",
                "stderr": "Command blocked by security policy",
                "exit_code": -1,
                "execution_time": 0.0
            }
        
        self.logger.info(f"Executing command: {command}")
        start_time = time.time()
        
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True,
                executable=self.config.execution.shell,
                cwd=os.path.expanduser(self.config.execution.working_directory)
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                exit_code = process.returncode
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Command timeout: {command}")
                process.kill()
                await process.wait()
                return {
                    "stdout": "",
                    "stderr": f"Command timeout after {timeout} seconds",
                    "exit_code": -1,
                    "execution_time": timeout
                }
            
            execution_time = time.time() - start_time
            
            result = {
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "exit_code": exit_code,
                "execution_time": round(execution_time, 3)
            }
            
            self.logger.info(f"Command completed: exit_code={exit_code}, time={execution_time:.3f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            execution_time = time.time() - start_time
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "execution_time": round(execution_time, 3)
            }
    
    def _is_command_allowed(self, command: str) -> bool:
        """
        Check if command is allowed based on security settings.
        
        Args:
            command: Command to check
            
        Returns:
            True if command is allowed, False otherwise
        """
        # Check blocked commands
        if self.config.security.blocked_commands:
            for blocked in self.config.security.blocked_commands:
                if blocked in command:
                    return False
        
        # Check allowed commands (if whitelist is enabled)
        if self.config.security.allowed_commands:
            is_allowed = False
            for allowed_cmd in self.config.security.allowed_commands:
                if command.startswith(allowed_cmd):
                    is_allowed = True
                    break
            return is_allowed
        
        return True
