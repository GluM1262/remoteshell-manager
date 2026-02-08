"""SQLite database manager for command history and device tracking."""

import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for command history and device tracking."""
    
    def __init__(self, db_path: str = "remoteshell.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        
    async def initialize(self) -> None:
        """Initialize database and create tables."""
        try:
            # Read schema file
            schema_path = Path(__file__).parent / "schemas.sql"
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            # Create database and tables
            async with aiosqlite.connect(self.db_path) as db:
                await db.executescript(schema)
                await db.commit()
            
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def get_connection(self) -> aiosqlite.Connection:
        """Get database connection."""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
        return self._connection
    
    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Database connection closed")
    
    async def register_device(
        self,
        device_id: str,
        device_token: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register or update device in database.
        
        Args:
            device_id: Unique device identifier
            device_token: Device authentication token
            metadata: Additional device metadata
        """
        try:
            db = await self.get_connection()
            metadata_json = json.dumps(metadata) if metadata else None
            
            await db.execute(
                """
                INSERT INTO devices (device_id, device_token, metadata, last_connected)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(device_id) DO UPDATE SET
                    device_token = excluded.device_token,
                    metadata = excluded.metadata,
                    last_connected = CURRENT_TIMESTAMP
                """,
                (device_id, device_token, metadata_json)
            )
            await db.commit()
            logger.info(f"Device {device_id} registered/updated")
        except Exception as e:
            logger.error(f"Failed to register device {device_id}: {e}")
            raise
    
    async def update_device_status(self, device_id: str, status: str) -> None:
        """
        Update device online/offline status.
        
        Args:
            device_id: Device identifier
            status: New status ('online' or 'offline')
        """
        try:
            db = await self.get_connection()
            await db.execute(
                """
                UPDATE devices
                SET status = ?, last_connected = CURRENT_TIMESTAMP
                WHERE device_id = ?
                """,
                (status, device_id)
            )
            await db.commit()
            logger.debug(f"Device {device_id} status updated to {status}")
        except Exception as e:
            logger.error(f"Failed to update device status for {device_id}: {e}")
            raise
    
    async def create_command(
        self,
        command_id: str,
        device_id: str,
        command: str
    ) -> int:
        """
        Create new command entry.
        
        Args:
            command_id: Unique command identifier
            device_id: Target device identifier
            command: Command to execute
            
        Returns:
            Command database ID
        """
        try:
            db = await self.get_connection()
            cursor = await db.execute(
                """
                INSERT INTO commands (command_id, device_id, command, status)
                VALUES (?, ?, ?, 'pending')
                """,
                (command_id, device_id, command)
            )
            await db.commit()
            logger.info(f"Command {command_id} created for device {device_id}")
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create command {command_id}: {e}")
            raise
    
    async def update_command_status(
        self,
        command_id: str,
        status: str,
        **kwargs
    ) -> None:
        """
        Update command status and results.
        
        Args:
            command_id: Command identifier
            status: New status
            **kwargs: Additional fields to update (sent_at, completed_at, stdout, stderr, exit_code, execution_time, error_message)
        """
        try:
            db = await self.get_connection()
            
            # Build update query dynamically
            fields = ["status = ?"]
            values = [status]
            
            # Add timestamp for status changes
            if status == "sent":
                fields.append("sent_at = CURRENT_TIMESTAMP")
            elif status in ("completed", "failed", "timeout"):
                fields.append("completed_at = CURRENT_TIMESTAMP")
            
            # Add optional fields
            for key, value in kwargs.items():
                if key in ("stdout", "stderr", "exit_code", "execution_time", "error_message"):
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            query = f"UPDATE commands SET {', '.join(fields)} WHERE command_id = ?"
            values.append(command_id)
            
            await db.execute(query, tuple(values))
            await db.commit()
            logger.debug(f"Command {command_id} updated: status={status}")
        except Exception as e:
            logger.error(f"Failed to update command {command_id}: {e}")
            raise
    
    async def get_command(self, command_id: str) -> Optional[Dict[str, Any]]:
        """
        Get command by ID.
        
        Args:
            command_id: Command identifier
            
        Returns:
            Command data or None if not found
        """
        try:
            db = await self.get_connection()
            async with db.execute(
                "SELECT * FROM commands WHERE command_id = ?",
                (command_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Failed to get command {command_id}: {e}")
            raise
    
    async def get_device_commands(
        self,
        device_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get command history for device.
        
        Args:
            device_id: Device identifier
            limit: Maximum number of commands to return
            
        Returns:
            List of command records
        """
        try:
            db = await self.get_connection()
            async with db.execute(
                """
                SELECT * FROM commands
                WHERE device_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (device_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get commands for device {device_id}: {e}")
            raise
    
    async def get_pending_commands(self, device_id: str) -> List[Dict[str, Any]]:
        """
        Get pending commands for device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            List of pending command records
        """
        try:
            db = await self.get_connection()
            async with db.execute(
                """
                SELECT * FROM commands
                WHERE device_id = ? AND status = 'pending'
                ORDER BY created_at ASC
                """,
                (device_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get pending commands for device {device_id}: {e}")
            raise
    
    async def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device information.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device data or None if not found
        """
        try:
            db = await self.get_connection()
            async with db.execute(
                "SELECT * FROM devices WHERE device_id = ?",
                (device_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    device = dict(row)
                    # Parse metadata JSON
                    if device.get('metadata'):
                        device['metadata'] = json.loads(device['metadata'])
                    return device
                return None
        except Exception as e:
            logger.error(f"Failed to get device info for {device_id}: {e}")
            raise
    
    async def get_all_devices(self) -> List[Dict[str, Any]]:
        """
        Get all registered devices.
        
        Returns:
            List of device records
        """
        try:
            db = await self.get_connection()
            async with db.execute("SELECT * FROM devices ORDER BY last_connected DESC") as cursor:
                rows = await cursor.fetchall()
                devices = []
                for row in rows:
                    device = dict(row)
                    # Parse metadata JSON
                    if device.get('metadata'):
                        device['metadata'] = json.loads(device['metadata'])
                    devices.append(device)
                return devices
        except Exception as e:
            logger.error(f"Failed to get all devices: {e}")
            raise
    
    async def delete_command(self, command_id: str) -> bool:
        """
        Delete command from database.
        
        Args:
            command_id: Command identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            db = await self.get_connection()
            cursor = await db.execute(
                "DELETE FROM commands WHERE command_id = ? AND status = 'pending'",
                (command_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete command {command_id}: {e}")
            raise
    
    async def get_commands_with_filters(
        self,
        device_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get commands with filters.
        
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
            db = await self.get_connection()
            
            query = "SELECT * FROM commands WHERE 1=1"
            params = []
            
            if device_id:
                query += " AND device_id = ?"
                params.append(device_id)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND created_at <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            async with db.execute(query, tuple(params)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get commands with filters: {e}")
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
            Statistics dictionary
        """
        try:
            db = await self.get_connection()
            
            where_clause = "WHERE device_id = ?" if device_id else ""
            params = (device_id,) if device_id else ()
            
            async with db.execute(
                f"""
                SELECT
                    COUNT(*) as total_commands,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeout,
                    AVG(CASE WHEN execution_time IS NOT NULL THEN execution_time ELSE NULL END) as avg_execution_time
                FROM commands
                {where_clause}
                """,
                params
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else {}
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
            db = await self.get_connection()
            cursor = await db.execute(
                """
                DELETE FROM commands
                WHERE created_at < datetime('now', ? || ' days')
                """,
                (f'-{days}',)
            )
            await db.commit()
            deleted_count = cursor.rowcount
            logger.info(f"Cleaned up {deleted_count} old command records")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            raise
