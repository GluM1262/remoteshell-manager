"""FastAPI application for RemoteShell Manager server."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional, List
from datetime import datetime

try:
    from .config import settings
    from .database import Database
    from .queue_manager import QueueManager
    from .history import HistoryManager
    from .websocket_handler import ConnectionManager
    from .models import (
        SendCommandRequest,
        CommandResponse,
        CommandStatus,
        DeviceStatus,
        HistoryQuery,
        Statistics,
        CleanupRequest,
        ExportRequest,
        BulkCommandRequest,
    )
except ImportError:
    from config import settings
    from database import Database
    from queue_manager import QueueManager
    from history import HistoryManager
    from websocket_handler import ConnectionManager
    from models import (
        SendCommandRequest,
        CommandResponse,
        CommandStatus,
        DeviceStatus,
        HistoryQuery,
        Statistics,
        CleanupRequest,
        ExportRequest,
        BulkCommandRequest,
    )

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
database: Optional[Database] = None
queue_manager: Optional[QueueManager] = None
history_manager: Optional[HistoryManager] = None
connection_manager: Optional[ConnectionManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global database, queue_manager, history_manager, connection_manager
    
    # Startup
    logger.info("Starting RemoteShell Manager server...")
    
    # Initialize database
    database = Database(settings.database_path)
    await database.initialize()
    
    # Initialize managers
    queue_manager = QueueManager(database)
    history_manager = HistoryManager(database)
    connection_manager = ConnectionManager(database, queue_manager)
    
    logger.info(f"Server started on {settings.host}:{settings.port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down server...")
    await database.close()
    logger.info("Server stopped")


# Create FastAPI app
app = FastAPI(
    title="RemoteShell Manager",
    description="Remote Linux device management system via WebSocket",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "RemoteShell Manager",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# WebSocket endpoint for device connections
@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str, token: str = Query(...)):
    """
    WebSocket endpoint for device connections.
    
    Args:
        websocket: WebSocket connection
        device_id: Device identifier
        token: Authentication token
    """
    logger.info(f"WebSocket connection attempt from device {device_id}")
    
    # Connect device
    connected = await connection_manager.connect(device_id, token, websocket)
    
    if not connected:
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    try:
        # Listen for messages
        while True:
            message = await websocket.receive_json()
            await connection_manager.handle_message(device_id, message)
            
    except WebSocketDisconnect:
        logger.info(f"Device {device_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for device {device_id}: {e}")
    finally:
        await connection_manager.disconnect(device_id)


# Command management endpoints
@app.post("/api/command", response_model=CommandResponse)
async def send_command(request: SendCommandRequest):
    """
    Send command to device.
    
    Args:
        request: Command request
        
    Returns:
        Command response with command_id
    """
    try:
        # Verify device exists
        device_info = await database.get_device_info(request.device_id)
        if not device_info:
            raise HTTPException(status_code=404, detail=f"Device {request.device_id} not found")
        
        # Add command to queue
        command_id = await queue_manager.add_command(
            request.device_id,
            request.command,
            timeout=request.timeout or settings.command_default_timeout,
            priority=request.priority or 0
        )
        
        return CommandResponse(
            command_id=command_id,
            status="pending",
            message="Command queued successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/command/{command_id}", response_model=CommandStatus)
async def get_command_status(command_id: str):
    """
    Get command status.
    
    Args:
        command_id: Command identifier
        
    Returns:
        Command status
    """
    try:
        command = await database.get_command(command_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        
        # Parse timestamps
        for field in ["created_at", "sent_at", "completed_at"]:
            if command.get(field):
                command[field] = datetime.fromisoformat(command[field])
        
        return CommandStatus(**command)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting command status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commands", response_model=List[CommandStatus])
async def get_commands(
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get command history with filters.
    
    Args:
        device_id: Filter by device ID
        status: Filter by status
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of results
        
    Returns:
        List of commands
    """
    try:
        commands = await history_manager.get_history(
            device_id=device_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        # Parse timestamps
        result = []
        for cmd in commands:
            for field in ["created_at", "sent_at", "completed_at"]:
                if cmd.get(field):
                    cmd[field] = datetime.fromisoformat(cmd[field])
            result.append(CommandStatus(**cmd))
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting commands: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/command/{command_id}")
async def cancel_command(command_id: str):
    """
    Cancel pending command.
    
    Args:
        command_id: Command identifier
        
    Returns:
        Success message
    """
    try:
        # Check if command exists and is pending
        command = await database.get_command(command_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        
        if command['status'] != 'pending':
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel command with status {command['status']}"
            )
        
        # Delete command
        deleted = await database.delete_command(command_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Command not found or already processed")
        
        return {"message": "Command cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/commands/bulk", response_model=List[CommandResponse])
async def send_bulk_commands(request: BulkCommandRequest):
    """
    Send command to multiple devices.
    
    Args:
        request: Bulk command request
        
    Returns:
        List of command responses
    """
    try:
        results = []
        
        for device_id in request.device_ids:
            try:
                # Verify device exists
                device_info = await database.get_device_info(device_id)
                if not device_info:
                    logger.warning(f"Device {device_id} not found, skipping")
                    results.append(CommandResponse(
                        command_id="",
                        status="error",
                        message=f"Device {device_id} not found"
                    ))
                    continue
                
                # Add command to queue
                command_id = await queue_manager.add_command(
                    device_id,
                    request.command,
                    timeout=request.timeout or settings.command_default_timeout,
                    priority=request.priority or 0
                )
                
                results.append(CommandResponse(
                    command_id=command_id,
                    status="pending",
                    message="Command queued successfully"
                ))
                
            except Exception as e:
                logger.error(f"Error sending command to device {device_id}: {e}")
                results.append(CommandResponse(
                    command_id="",
                    status="error",
                    message=str(e)
                ))
        
        return results
        
    except Exception as e:
        logger.error(f"Error sending bulk commands: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Device management endpoints
@app.get("/api/devices", response_model=List[DeviceStatus])
async def list_devices():
    """
    List all devices with status.
    
    Returns:
        List of devices
    """
    try:
        devices = await database.get_all_devices()
        
        result = []
        for device in devices:
            # Get queue size
            queue_size = await queue_manager.get_queue_size(device['device_id'])
            
            # Get command count
            stats = await history_manager.get_statistics(device['device_id'])
            
            # Parse timestamps
            first_seen = datetime.fromisoformat(device['first_seen'])
            last_connected = datetime.fromisoformat(device['last_connected'])
            
            result.append(DeviceStatus(
                device_id=device['device_id'],
                status=device['status'],
                first_seen=first_seen,
                last_connected=last_connected,
                queue_size=queue_size,
                total_commands=stats['total_commands'],
                metadata=device.get('metadata')
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/devices/{device_id}", response_model=DeviceStatus)
async def get_device(device_id: str):
    """
    Get device details.
    
    Args:
        device_id: Device identifier
        
    Returns:
        Device status
    """
    try:
        device = await database.get_device_info(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Get queue size
        queue_size = await queue_manager.get_queue_size(device_id)
        
        # Get command count
        stats = await history_manager.get_statistics(device_id)
        
        # Parse timestamps
        first_seen = datetime.fromisoformat(device['first_seen'])
        last_connected = datetime.fromisoformat(device['last_connected'])
        
        return DeviceStatus(
            device_id=device['device_id'],
            status=device['status'],
            first_seen=first_seen,
            last_connected=last_connected,
            queue_size=queue_size,
            total_commands=stats['total_commands'],
            metadata=device.get('metadata')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/devices/{device_id}/queue")
async def get_device_queue(device_id: str):
    """
    Get device queue status.
    
    Args:
        device_id: Device identifier
        
    Returns:
        Queue status
    """
    try:
        device = await database.get_device_info(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        queue_size = await queue_manager.get_queue_size(device_id)
        pending_commands = await database.get_pending_commands(device_id)
        
        return {
            "device_id": device_id,
            "queue_size": queue_size,
            "pending_commands": pending_commands,
            "is_connected": connection_manager.is_connected(device_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/devices/{device_id}/history", response_model=List[CommandStatus])
async def get_device_history(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get device command history.
    
    Args:
        device_id: Device identifier
        limit: Maximum number of results
        
    Returns:
        List of commands
    """
    try:
        device = await database.get_device_info(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        commands = await database.get_device_commands(device_id, limit)
        
        # Parse timestamps
        result = []
        for cmd in commands:
            for field in ["created_at", "sent_at", "completed_at"]:
                if cmd.get(field):
                    cmd[field] = datetime.fromisoformat(cmd[field])
            result.append(CommandStatus(**cmd))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/devices/{device_id}/statistics", response_model=Statistics)
async def get_device_statistics(device_id: str):
    """
    Get device statistics.
    
    Args:
        device_id: Device identifier
        
    Returns:
        Device statistics
    """
    try:
        device = await database.get_device_info(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        stats = await history_manager.get_statistics(device_id)
        return Statistics(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# History endpoints
@app.get("/api/history", response_model=List[CommandStatus])
async def get_history(
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get global command history.
    
    Args:
        device_id: Filter by device ID
        status: Filter by status
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of results
        
    Returns:
        List of commands
    """
    return await get_commands(device_id, status, start_date, end_date, limit)


@app.get("/api/statistics", response_model=Statistics)
async def get_statistics():
    """
    Get global statistics.
    
    Returns:
        Global statistics
    """
    try:
        stats = await history_manager.get_statistics()
        return Statistics(**stats)
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/history/cleanup")
async def cleanup_history(request: CleanupRequest):
    """
    Cleanup old records.
    
    Args:
        request: Cleanup request with days parameter
        
    Returns:
        Number of deleted records
    """
    try:
        deleted_count = await history_manager.cleanup_old_records(request.days)
        return {
            "message": f"Deleted {deleted_count} old records",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/export")
async def export_history(
    format: str = Query("json", pattern="^(json|csv)$"),
    device_id: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000)
):
    """
    Export history.
    
    Args:
        format: Export format (json or csv)
        device_id: Filter by device ID
        limit: Maximum number of records
        
    Returns:
        Exported data
    """
    try:
        data = await history_manager.export_history(format, device_id, limit)
        
        # Return with appropriate content type
        if format == "json":
            from fastapi.responses import JSONResponse
            import json
            return JSONResponse(content=json.loads(data))
        else:
            from fastapi.responses import Response
            return Response(content=data, media_type="text/csv")
        
    except Exception as e:
        logger.error(f"Error exporting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
