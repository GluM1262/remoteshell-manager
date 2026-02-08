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
            logger.info(f"Device registered: {device_id}")
        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            raise
    
    async def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device information.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device information dictionary or None
        """
        try:
            db = await self.get_connection()
            async with db.execute(
                "SELECT * FROM devices WHERE device_id = ?",
                (device_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    device_dict = dict(row)
                    if device_dict.get('metadata'):
                        device_dict['metadata'] = json.loads(device_dict['metadata'])
                    return device_dict
                return None
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            raise
    
    async def get_all_devices(self) -> List[Dict[str, Any]]:
        """
        Get all registered devices.
        
        Returns:
            List of device dictionaries
        """
        try:
            db = await self.get_connection()
            async with db.execute("SELECT * FROM devices ORDER BY last_connected DESC") as cursor:
                rows = await cursor.fetchall()
                devices = []
                for row in rows:
                    device_dict = dict(row)
                    if device_dict.get('metadata'):
                        device_dict['metadata'] = json.loads(device_dict['metadata'])
                    devices.append(device_dict)
                return devices
        except Exception as e:
            logger.error(f"Failed to get all devices: {e}")
            raise
    
    async def update_device_status(
        self,
        device_id: str,
        status: str
    ) -> None:
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
            logger.error(f"Failed to update device status: {e}")
            raise
    
    async def add_command(
        self,
        command_id: str,
        device_id: str,
        command: str,
        timeout: int = 30,
        priority: int = 0
    ) -> None:
        """
        Add command to database.
        
        Args:
            command_id: Unique command identifier
            device_id: Target device identifier
            command: Command string
            timeout: Command timeout in seconds
            priority: Command priority
        """
        try:
            db = await self.get_connection()
            await db.execute(
                """
                INSERT INTO commands (
                    command_id, device_id, command, status, timeout, priority, created_at
                )
                VALUES (?, ?, ?, 'pending', ?, ?, CURRENT_TIMESTAMP)
                """,
                (command_id, device_id, command, timeout, priority)
            )
            await db.commit()
            logger.debug(f"Command added: {command_id}")
        except Exception as e:
            logger.error(f"Failed to add command: {e}")
            raise
    
    async def update_command_status(
        self,
        command_id: str,
        status: str,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        exit_code: Optional[int] = None,
        execution_time: Optional[float] = None
    ) -> None:
        """
        Update command execution status.
        
        Args:
            command_id: Command identifier
            status: New status
            stdout: Standard output
            stderr: Standard error
            exit_code: Exit code
            execution_time: Execution time in seconds
        """
        try:
            db = await self.get_connection()
            
            # Build update query dynamically
            updates = ["status = ?"]
            params = [status]
            
            if stdout is not None:
                updates.append("stdout = ?")
                params.append(stdout)
            
            if stderr is not None:
                updates.append("stderr = ?")
                params.append(stderr)
            
            if exit_code is not None:
                updates.append("exit_code = ?")
                params.append(exit_code)
            
            if execution_time is not None:
                updates.append("execution_time = ?")
                params.append(execution_time)
            
            if status in ['completed', 'failed', 'timeout']:
                updates.append("completed_at = CURRENT_TIMESTAMP")
            elif status == 'running':
                updates.append("started_at = CURRENT_TIMESTAMP")
            
            params.append(command_id)
            
            query = f"UPDATE commands SET {', '.join(updates)} WHERE command_id = ?"
            
            await db.execute(query, tuple(params))
            await db.commit()
            logger.debug(f"Command {command_id} status updated to {status}")
        except Exception as e:
            logger.error(f"Failed to update command status: {e}")
            raise
    
    async def get_command(self, command_id: str) -> Optional[Dict[str, Any]]:
        """
        Get command information.
        
        Args:
            command_id: Command identifier
            
        Returns:
            Command dictionary or None
        """
        try:
            db = await self.get_connection()
            async with db.execute(
                "SELECT * FROM commands WHERE command_id = ?",
                (command_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get command: {e}")
            raise
    
    async def get_device_commands(
        self,
        device_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get commands for a specific device.
        
        Args:
            device_id: Device identifier
            limit: Maximum number of records
            offset: Offset for pagination
            
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
                LIMIT ? OFFSET ?
                """,
                (device_id, limit, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get device commands: {e}")
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
        Get commands with optional filters.
        
        Args:
            device_id: Optional device ID filter
            status: Optional status filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of records
            
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
