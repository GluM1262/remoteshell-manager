"""
Database module for storing device information, command history, and queue.
Uses SQLite for simplicity and portability.
"""

import sqlite3
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)


class Database:
    """
    Database manager for RemoteShell Manager.
    Stores devices, command history, and command queue.
    """
    
    def __init__(self, db_path: str = "remoteshell.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
        
    async def connect(self):
        """Connect to database and create tables."""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            self.connection.row_factory = sqlite3.Row
            await self._create_tables()
            logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables if they don't exist."""
        async with self._lock:
            cursor = self.connection.cursor()
            
            # Devices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE NOT NULL,
                    token TEXT NOT NULL,
                    status TEXT DEFAULT 'offline',
                    last_seen TIMESTAMP,
                    first_connected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hostname TEXT,
                    ip_address TEXT,
                    metadata TEXT
                )
            """)
            
            # Command history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    command TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    stdout TEXT,
                    stderr TEXT,
                    exit_code INTEGER,
                    execution_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )
            """)
            
            # Command queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    command TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    timeout INTEGER,
                    status TEXT DEFAULT 'queued',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices(device_id)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_id ON devices(device_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_command_history_device ON command_history(device_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_command_queue_device ON command_queue(device_id, status)")
            
            self.connection.commit()
            logger.info("Database tables created/verified")
    
    async def register_device(
        self,
        device_id: str,
        token: str,
        hostname: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Register or update device in database.
        
        Args:
            device_id: Unique device identifier
            token: Authentication token
            hostname: Device hostname
            ip_address: Device IP address
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                cursor = self.connection.cursor()
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute("""
                    INSERT INTO devices (device_id, token, hostname, ip_address, metadata, last_seen)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(device_id) DO UPDATE SET
                        token = excluded.token,
                        hostname = excluded.hostname,
                        ip_address = excluded.ip_address,
                        metadata = excluded.metadata,
                        last_seen = CURRENT_TIMESTAMP
                """, (device_id, token, hostname, ip_address, metadata_json))
                
                self.connection.commit()
                logger.info(f"Device registered: {device_id}")
                return True
            except Exception as e:
                logger.error(f"Error registering device {device_id}: {e}")
                return False
    
    async def update_device_status(self, device_id: str, status: str) -> bool:
        """
        Update device status.
        
        Args:
            device_id: Device identifier
            status: New status (online/offline)
            
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute("""
                    UPDATE devices 
                    SET status = ?, last_seen = CURRENT_TIMESTAMP
                    WHERE device_id = ?
                """, (status, device_id))
                
                self.connection.commit()
                return True
            except Exception as e:
                logger.error(f"Error updating device status: {e}")
                return False
    
    async def get_device(self, device_id: str) -> Optional[Dict]:
        """
        Get device information.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device dict or None
        """
        async with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
            except Exception as e:
                logger.error(f"Error getting device: {e}")
                return None
    
    async def list_devices(self) -> List[Dict]:
        """
        List all devices.
        
        Returns:
            List of device dicts
        """
        async with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute("SELECT * FROM devices ORDER BY last_seen DESC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Error listing devices: {e}")
                return []
    
    async def add_command_history(
        self,
        device_id: str,
        command: str,
        status: str = 'pending',
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        exit_code: Optional[int] = None,
        execution_time: Optional[float] = None
    ) -> Optional[int]:
        """
        Add command to history.
        
        Returns:
            Command ID if successful
        """
        async with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO command_history 
                    (device_id, command, status, stdout, stderr, exit_code, execution_time, executed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (device_id, command, status, stdout, stderr, exit_code, execution_time))
                
                self.connection.commit()
                return cursor.lastrowid
            except Exception as e:
                logger.error(f"Error adding command history: {e}")
                return None
    
    async def update_command_history(
        self,
        command_id: int,
        status: str,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        exit_code: Optional[int] = None,
        execution_time: Optional[float] = None
    ) -> bool:
        """Update command history entry."""
        async with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute("""
                    UPDATE command_history
                    SET status = ?, stdout = ?, stderr = ?, exit_code = ?, 
                        execution_time = ?, executed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, stdout, stderr, exit_code, execution_time, command_id))
                
                self.connection.commit()
                return True
            except Exception as e:
                logger.error(f"Error updating command history: {e}")
                return False
    
    async def get_command_history(
        self,
        device_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get command history.
        
        Args:
            device_id: Filter by device (optional)
            limit: Maximum number of records
            offset: Pagination offset
            
        Returns:
            List of command history records
        """
        async with self._lock:
            try:
                cursor = self.connection.cursor()
                if device_id:
                    cursor.execute("""
                        SELECT * FROM command_history 
                        WHERE device_id = ?
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    """, (device_id, limit, offset))
                else:
                    cursor.execute("""
                        SELECT * FROM command_history 
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    """, (limit, offset))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Error getting command history: {e}")
                return []
    
    async def queue_command(
        self,
        device_id: str,
        command: str,
        timeout: Optional[int] = None,
        priority: int = 0
    ) -> Optional[int]:
        """
        Add command to queue for offline device.
        
        Returns:
            Queue entry ID if successful
        """
        async with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO command_queue (device_id, command, timeout, priority)
                    VALUES (?, ?, ?, ?)
                """, (device_id, command, timeout, priority))
                
                self.connection.commit()
                logger.info(f"Command queued for {device_id}: {command}")
                return cursor.lastrowid
            except Exception as e:
                logger.error(f"Error queuing command: {e}")
                return None
    
    async def get_queued_commands(self, device_id: str) -> List[Dict]:
        """
        Get all queued commands for a device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            List of queued commands
        """
        async with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute("""
                    SELECT * FROM command_queue
                    WHERE device_id = ? AND status = 'queued'
                    ORDER BY priority DESC, created_at ASC
                """, (device_id,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Error getting queued commands: {e}")
                return []
    
    async def dequeue_command(self, queue_id: int) -> bool:
        """
        Mark command as sent (remove from queue).
        
        Args:
            queue_id: Queue entry ID
            
        Returns:
            True if successful
        """
        async with self._lock:
            try:
                cursor = self.connection.cursor()
                cursor.execute("""
                    UPDATE command_queue
                    SET status = 'sent'
                    WHERE id = ?
                """, (queue_id,))
                
                self.connection.commit()
                return True
            except Exception as e:
                logger.error(f"Error dequeuing command: {e}")
                return False
    
    async def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
