"""
Queue manager for offline device command queueing.
"""

import asyncio
from typing import Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Manages command queue for offline devices.
    When a device reconnects, queued commands are sent automatically.
    """
"""Command queue manager for device command orchestration."""

import asyncio
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging

try:
    from .config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)


@dataclass
class QueuedCommand:
    """Represents a queued command."""
    command_id: str
    device_id: str
    command: str
    timeout: int
    created_at: datetime
    priority: int = 0
    
    def __lt__(self, other):
        """Compare by priority (higher priority first)."""
        return self.priority > other.priority


class QueueManager:
    """Manages command queues for all devices."""
    
    def __init__(self, database):
        """
        Initialize queue manager.
        
        Args:
            database: Database instance
        """
        self.database = database
        self.connection_callbacks: Dict[str, List[Callable]] = {}
        logger.info("Queue manager initialized")
    
    async def queue_command_for_device(
        self,
        device_id: str,
        command: str,
        timeout: Optional[int] = None,
        priority: int = 0
    ) -> bool:
        """
        Queue command for offline device.
            database: Database instance for persistence
        """
        self.database = database
        self.queues: Dict[str, asyncio.Queue] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        
    def _get_queue(self, device_id: str) -> asyncio.Queue:
        """
        Get or create queue for device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Queue for device
        """
        if device_id not in self.queues:
            self.queues[device_id] = asyncio.Queue()
            logger.debug(f"Created queue for device {device_id}")
        return self.queues[device_id]
    
    def _get_lock(self, device_id: str) -> asyncio.Lock:
        """
        Get or create lock for device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Lock for device
        """
        if device_id not in self._locks:
            self._locks[device_id] = asyncio.Lock()
        return self._locks[device_id]
    
    async def add_command(
        self,
        device_id: str,
        command: str,
        timeout: int = 30,
        priority: int = 0
    ) -> str:
        """
        Add command to device queue.
        
        Args:
            device_id: Target device identifier
            command: Command to execute
            timeout: Optional execution timeout
            priority: Command priority (higher = more urgent)
            
        Returns:
            True if queued successfully
        """
        queue_id = await self.database.queue_command(
            device_id=device_id,
            command=command,
            timeout=timeout,
            priority=priority
        )
        
        if queue_id:
            logger.info(f"Command queued for {device_id} with ID {queue_id}")
            return True
        return False
    
    async def process_queued_commands(
        self,
        device_id: str,
        send_callback: Callable
    ) -> int:
        """
        Process all queued commands for a device when it reconnects.
        
        Args:
            device_id: Device that reconnected
            send_callback: Async function to send command to device
            
        Returns:
            Number of commands sent
        """
        commands = await self.database.get_queued_commands(device_id)
        
        if not commands:
            logger.info(f"No queued commands for {device_id}")
            return 0
        
        logger.info(f"Processing {len(commands)} queued commands for {device_id}")
        sent_count = 0
        
        for cmd in commands:
            try:
                # Send command to device
                await send_callback({
                    "type": "command",
                    "command": cmd["command"],
                    "timeout": cmd["timeout"],
                    "queue_id": cmd["id"]
                })
                
                # Mark as sent
                await self.database.dequeue_command(cmd["id"])
                sent_count += 1
                
                logger.info(f"Sent queued command {cmd['id']} to {device_id}")
                
            except Exception as e:
                logger.error(f"Error sending queued command {cmd['id']}: {e}")
        
        return sent_count
    
    async def get_queue_status(self, device_id: str) -> Dict:
        """
        Get queue status for a device.
            timeout: Command timeout in seconds
            priority: Command priority (higher = more important)
            
        Returns:
            command_id: Unique command identifier
        """
        try:
            # Generate unique command ID
            command_id = f"cmd_{uuid.uuid4().hex[:12]}"
            
            # Create command in database
            await self.database.create_command(command_id, device_id, command)
            
            # Add to queue
            queued_cmd = QueuedCommand(
                command_id=command_id,
                device_id=device_id,
                command=command,
                timeout=timeout,
                created_at=datetime.utcnow(),
                priority=priority
            )
            
            queue = self._get_queue(device_id)
            await queue.put(queued_cmd)
            
            logger.info(f"Command {command_id} added to queue for device {device_id}")
            return command_id
        except Exception as e:
            logger.error(f"Failed to add command to queue: {e}")
            raise
    
    async def get_next_command(self, device_id: str) -> Optional[QueuedCommand]:
        """
        Get next command from device queue.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Next queued command or None if queue is empty
        """
        try:
            queue = self._get_queue(device_id)
            
            if queue.empty():
                return None
            
            # Non-blocking get
            try:
                cmd = queue.get_nowait()
                logger.debug(f"Retrieved command {cmd.command_id} from queue")
                return cmd
            except asyncio.QueueEmpty:
                return None
        except Exception as e:
            logger.error(f"Failed to get next command: {e}")
            raise
    
    async def mark_command_sent(self, command_id: str) -> None:
        """
        Mark command as sent to device.
        
        Args:
            command_id: Command identifier
        """
        try:
            await self.database.update_command_status(command_id, "sent")
            logger.debug(f"Command {command_id} marked as sent")
        except Exception as e:
            logger.error(f"Failed to mark command as sent: {e}")
            raise
    
    async def complete_command(
        self,
        command_id: str,
        stdout: str,
        stderr: str,
        exit_code: int,
        execution_time: float
    ) -> None:
        """
        Mark command as completed with results.
        
        Args:
            command_id: Command identifier
            stdout: Command standard output
            stderr: Command standard error
            exit_code: Command exit code
            execution_time: Execution time in seconds
        """
        try:
            await self.database.update_command_status(
                command_id,
                "completed",
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time=execution_time
            )
            logger.info(f"Command {command_id} completed with exit code {exit_code}")
        except Exception as e:
            logger.error(f"Failed to complete command: {e}")
            raise
    
    async def fail_command(self, command_id: str, error_message: str) -> None:
        """
        Mark command as failed.
        
        Args:
            command_id: Command identifier
            error_message: Error description
        """
        try:
            await self.database.update_command_status(
                command_id,
                "failed",
                error_message=error_message
            )
            logger.warning(f"Command {command_id} failed: {error_message}")
        except Exception as e:
            logger.error(f"Failed to mark command as failed: {e}")
            raise
    
    async def timeout_command(self, command_id: str) -> None:
        """
        Mark command as timed out.
        
        Args:
            command_id: Command identifier
        """
        try:
            await self.database.update_command_status(
                command_id,
                "timeout",
                error_message="Command execution timed out"
            )
            logger.warning(f"Command {command_id} timed out")
        except Exception as e:
            logger.error(f"Failed to mark command as timeout: {e}")
            raise
    
    async def get_queue_size(self, device_id: str) -> int:
        """
        Get number of pending commands for device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Dict with queue statistics
        """
        commands = await self.database.get_queued_commands(device_id)
        
        return {
            "device_id": device_id,
            "queued_count": len(commands),
            "commands": [
                {
                    "id": cmd["id"],
                    "command": cmd["command"],
                    "priority": cmd["priority"],
                    "created_at": cmd["created_at"]
                }
                for cmd in commands
            ]
        }
    
    async def clear_queue(self, device_id: str) -> int:
        """
        Clear all queued commands for a device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Number of commands cleared
        """
        commands = await self.database.get_queued_commands(device_id)
        cleared = 0
        
        for cmd in commands:
            if await self.database.dequeue_command(cmd["id"]):
                cleared += 1
        
        logger.info(f"Cleared {cleared} commands from queue for {device_id}")
        return cleared
            Number of pending commands
        """
        try:
            queue = self._get_queue(device_id)
            return queue.qsize()
        except Exception as e:
            logger.error(f"Failed to get queue size: {e}")
            return 0
    
    async def start_processing(self, device_id: str, websocket) -> None:
        """
        Start processing queue for connected device.
        
        Args:
            device_id: Device identifier
            websocket: WebSocket connection to device
        """
        try:
            lock = self._get_lock(device_id)
            
            async with lock:
                # Stop any existing processing task
                if device_id in self.processing_tasks:
                    await self.stop_processing(device_id)
                
                # Load pending commands from database into queue
                await self._load_pending_commands(device_id)
                
                # Create processing task
                task = asyncio.create_task(
                    self._process_queue(device_id, websocket)
                )
                self.processing_tasks[device_id] = task
                
                logger.info(f"Started queue processing for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to start processing for {device_id}: {e}")
            raise
    
    async def stop_processing(self, device_id: str) -> None:
        """
        Stop processing queue when device disconnects.
        
        Args:
            device_id: Device identifier
        """
        try:
            if device_id in self.processing_tasks:
                task = self.processing_tasks[device_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.processing_tasks[device_id]
                logger.info(f"Stopped queue processing for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to stop processing for {device_id}: {e}")
    
    async def _load_pending_commands(self, device_id: str) -> None:
        """
        Load pending commands from database into queue.
        
        Args:
            device_id: Device identifier
        """
        try:
            pending_commands = await self.database.get_pending_commands(device_id)
            queue = self._get_queue(device_id)
            
            for cmd_data in pending_commands:
                queued_cmd = QueuedCommand(
                    command_id=cmd_data['command_id'],
                    device_id=cmd_data['device_id'],
                    command=cmd_data['command'],
                    timeout=settings.command_default_timeout,
                    created_at=datetime.fromisoformat(cmd_data['created_at']),
                    priority=0
                )
                await queue.put(queued_cmd)
            
            if pending_commands:
                logger.info(f"Loaded {len(pending_commands)} pending commands for device {device_id}")
        except Exception as e:
            logger.error(f"Failed to load pending commands: {e}")
    
    async def _process_queue(self, device_id: str, websocket) -> None:
        """
        Process commands from queue and send to device.
        
        Args:
            device_id: Device identifier
            websocket: WebSocket connection
        """
        logger.debug(f"Queue processor started for device {device_id}")
        
        try:
            while True:
                # Wait for next command
                queue = self._get_queue(device_id)
                cmd = await queue.get()
                
                try:
                    # Mark as sent
                    await self.mark_command_sent(cmd.command_id)
                    
                    # Send command via WebSocket
                    await websocket.send_json({
                        "type": "command",
                        "command_id": cmd.command_id,
                        "command": cmd.command,
                        "timeout": cmd.timeout
                    })
                    
                    logger.debug(f"Sent command {cmd.command_id} to device {device_id}")
                    
                    # Wait for result with timeout
                    try:
                        # The websocket handler will call complete_command or fail_command
                        # when it receives the result
                        await asyncio.sleep(0.1)  # Small delay to avoid tight loop
                    except asyncio.TimeoutError:
                        await self.timeout_command(cmd.command_id)
                        logger.warning(f"Command {cmd.command_id} timed out")
                    
                except Exception as e:
                    logger.error(f"Error processing command {cmd.command_id}: {e}")
                    await self.fail_command(cmd.command_id, str(e))
                finally:
                    queue.task_done()
                    
        except asyncio.CancelledError:
            logger.debug(f"Queue processor cancelled for device {device_id}")
            raise
        except Exception as e:
            logger.error(f"Queue processor error for device {device_id}: {e}")
