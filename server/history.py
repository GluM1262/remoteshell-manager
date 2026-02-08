"""Command history management and analytics."""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
import csv
from io import StringIO
import logging

logger = logging.getLogger(__name__)


class HistoryManager:
    """Manages command history and analytics."""
    
    def __init__(self, database):
        """
        Initialize history manager.
        
        Args:
            database: Database instance
        """
        self.database = database
    
    async def get_history(
        self,
        device_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get filtered command history.
        
        Args:
            device_id: Filter by device ID
            status: Filter by status
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            
        Returns:
            List of command records
        """
        try:
            return await self.database.get_commands_with_filters(
                device_id=device_id,
                status=status,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            raise
    
    async def get_statistics(
        self,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get command execution statistics.
        
        Args:
            device_id: Optional device ID to filter statistics
            
        Returns:
            Statistics dictionary with:
                - total_commands: Total number of commands
                - completed: Number of completed commands
                - failed: Number of failed commands
                - pending: Number of pending commands
                - timeout: Number of timed out commands
                - avg_execution_time: Average execution time in seconds
        """
        try:
            stats = await self.database.get_statistics(device_id)
            
            # Ensure all fields are present
            return {
                "total_commands": stats.get("total_commands", 0) or 0,
                "completed": stats.get("completed", 0) or 0,
                "failed": stats.get("failed", 0) or 0,
                "pending": stats.get("pending", 0) or 0,
                "timeout": stats.get("timeout", 0) or 0,
                "avg_execution_time": stats.get("avg_execution_time", 0.0) or 0.0
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise
    
    async def cleanup_old_records(self, days: int = 30) -> int:
        """
        Delete records older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of deleted records
        """
        try:
            deleted_count = await self.database.cleanup_old_records(days)
            logger.info(f"Cleaned up {deleted_count} records older than {days} days")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            raise
    
    async def export_history(
        self,
        format: str = "json",
        device_id: Optional[str] = None,
        limit: int = 1000
    ) -> str:
        """
        Export history to JSON or CSV format.
        
        Args:
            format: Export format ('json' or 'csv')
            device_id: Optional device ID filter
            limit: Maximum number of records to export
            
        Returns:
            Exported data as string
        """
        try:
            # Get history data
            history = await self.get_history(
                device_id=device_id,
                limit=limit
            )
            
            if format.lower() == "json":
                return json.dumps(history, indent=2, default=str)
            elif format.lower() == "csv":
                return self._export_csv(history)
            else:
                raise ValueError(f"Unsupported export format: {format}")
        except Exception as e:
            logger.error(f"Failed to export history: {e}")
            raise
    
    def _export_csv(self, history: List[Dict[str, Any]]) -> str:
        """
        Export history to CSV format.
        
        Args:
            history: List of command records
            
        Returns:
            CSV string
        """
        if not history:
            return ""
        
        output = StringIO()
        
        # Define CSV fields
        fields = [
            "command_id", "device_id", "command", "status",
            "created_at", "sent_at", "completed_at",
            "stdout", "stderr", "exit_code", "execution_time", "error_message"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        
        for record in history:
            writer.writerow(record)
        
        return output.getvalue()
    
    async def get_device_summary(self, device_id: str) -> Dict[str, Any]:
        """
        Get comprehensive summary for a device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Summary with device info, statistics, and recent history
        """
        try:
            # Get device info
            device_info = await self.database.get_device_info(device_id)
            if not device_info:
                return None
            
            # Get statistics
            stats = await self.get_statistics(device_id)
            
            # Get recent history
            recent_history = await self.get_history(device_id=device_id, limit=10)
            
            return {
                "device": device_info,
                "statistics": stats,
                "recent_commands": recent_history
            }
        except Exception as e:
            logger.error(f"Failed to get device summary: {e}")
            raise
    
    async def get_global_summary(self) -> Dict[str, Any]:
        """
        Get global summary across all devices.
        
        Returns:
            Global statistics and device list
        """
        try:
            # Get all devices
            devices = await self.database.get_all_devices()
            
            # Get global statistics
            global_stats = await self.get_statistics()
            
            # Get device count by status
            online_count = sum(1 for d in devices if d.get('status') == 'online')
            offline_count = sum(1 for d in devices if d.get('status') == 'offline')
            
            return {
                "total_devices": len(devices),
                "online_devices": online_count,
                "offline_devices": offline_count,
                "global_statistics": global_stats,
                "devices": devices
            }
        except Exception as e:
            logger.error(f"Failed to get global summary: {e}")
            raise
