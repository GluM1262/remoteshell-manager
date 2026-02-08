"""
Shell command executor for server-side operations.
This module can be used to execute commands on the server itself or
to manage command execution requests.
"""

import asyncio
import subprocess
import logging
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


class ShellExecutor:
    """
    Executes shell commands on the server (for administrative tasks).
    Not used for remote device commands - those are executed on the client side.
    """
    
    def __init__(self, max_timeout: int = 60):
        """
        Initialize shell executor.
        
        Args:
            max_timeout: Maximum execution timeout in seconds
        """
        self.max_timeout = max_timeout
        logger.info(f"Shell executor initialized (max timeout: {max_timeout}s)")
    
    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict] = None
    ) -> Dict:
        """
        Execute shell command on server.
        
        Args:
            command: Command to execute
            timeout: Execution timeout
            cwd: Working directory
            env: Environment variables
            
        Returns:
            Dict with stdout, stderr, exit_code, execution_time
        """
        start_time = time.time()
        
        if timeout is None:
            timeout = self.max_timeout
        else:
            timeout = min(timeout, self.max_timeout)
        
        try:
            logger.info(f"Executing server command: {command}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                execution_time = time.time() - start_time
                
                result = {
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                    "exit_code": process.returncode,
                    "execution_time": execution_time,
                    "timed_out": False
                }
                
                logger.info(f"Command completed in {execution_time:.2f}s with code {process.returncode}")
                return result
            
            except asyncio.TimeoutError:
                # Kill the process
                process.kill()
                await process.wait()
                
                execution_time = time.time() - start_time
                logger.warning(f"Command timed out after {timeout}s")
                
                return {
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds",
                    "exit_code": -1,
                    "execution_time": execution_time,
                    "timed_out": True
                }
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing command: {e}")
            return {
                "stdout": "",
                "stderr": f"Error: {str(e)}",
                "exit_code": -1,
                "execution_time": execution_time,
                "timed_out": False
            }
    
    async def execute_safe(self, command: str) -> str:
        """
        Execute command and return stdout or error message.
        
        Args:
            command: Command to execute
            
        Returns:
            Command output or error message
        """
        result = await self.execute(command)
        
        if result["exit_code"] == 0:
            return result["stdout"].strip()
        else:
            return f"Error: {result['stderr']}"
