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
