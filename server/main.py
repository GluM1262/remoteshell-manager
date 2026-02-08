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
"""
FastAPI Main Application

Main entry point for the RemoteShell Manager server.
Provides WebSocket endpoint for command execution and REST API endpoints.
"""

import logging
import sys
from fastapi import FastAPI, WebSocket, WebSocketException, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from server.config import settings
from server.auth import validate_token, get_device_id, load_tokens_info
from server.websocket_handler import handle_websocket, manager
import uvicorn


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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


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
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting RemoteShell Manager Server")
    logger.info(f"Server running on {settings.host}:{settings.port}")
    
    # Load and log token information
    token_info = load_tokens_info()
    logger.info(f"Loaded {token_info['token_count']} device tokens")
    if token_info['device_ids']:
        logger.info(f"Configured devices: {', '.join(token_info['device_ids'])}")
    else:
        logger.warning("No device tokens configured! Add tokens to DEVICE_TOKENS environment variable")
    
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
    logger.info("Shutting down RemoteShell Manager Server")
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.websocket_handler import ConnectionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create connection manager instance
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("RemoteShell Manager server starting up...")
    yield
    # Shutdown
    logger.info("RemoteShell Manager server shutting down...")


# Initialize FastAPI application
app = FastAPI(
    title="RemoteShell Manager",
    description="WebSocket-based remote shell command execution server",
    description="Remote Linux device management via WebSocket",
    version="1.0.0",
    lifespan=lifespan
)


# Configure CORS middleware
# Note: In production, specify exact allowed origins instead of "*"
# For development/testing purposes, we allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Replace with specific origins in production
    allow_credentials=False,  # Disabled for wildcard origins
# Configure CORS
# WARNING: allow_origins=["*"] is insecure for production!
# In production, specify exact allowed origins, e.g., ["https://yourdomain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns server status and basic information.
    
    Example:
        GET /health
        
        Response:
        {
            "status": "healthy",
            "connected_devices": 2,
            "version": "1.0.0"
        }
    """
    return {
        "status": "healthy",
        "connected_devices": len(manager.active_connections),
        "version": "1.0.0"
    }


@app.get("/devices")
async def get_devices():
    """
    Get list of connected devices.
    
    Returns information about all currently connected devices.
    
    Example:
        GET /devices
        
        Response:
        {
            "devices": [
                {
                    "device_id": "device1",
                    "connected_at": "2024-01-01T12:00:00",
                    "last_command": "2024-01-01T12:05:00"
                }
            ],
            "count": 1
        }
    """
    devices = manager.get_connected_devices()
    return {
        "devices": devices,
        "count": len(devices)
    }


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Device authentication token")
):
    """
    WebSocket endpoint for command execution.
    
    Connection flow:
    1. Client connects with token: ws://localhost:8000/ws?token=DEVICE_TOKEN
    2. Server validates token
    3. If valid: accept connection and register device
    4. If invalid: reject connection with error message
    
    Message protocol:
    - Client sends: {"type": "command", "command": "ls -la", "id": "cmd_123"}
    - Server responds: {"type": "response", "id": "cmd_123", "stdout": "...", "stderr": "...", "exit_code": 0}
    - Error message: {"type": "error", "message": "error description"}
    
    Args:
        websocket: WebSocket connection
        token: Device authentication token (query parameter)
    
    Raises:
        WebSocketException: If token is invalid
    
    Example usage with websocat:
        websocat "ws://localhost:8000/ws?token=abc123token"
        
        Send command:
        {"type": "command", "command": "echo hello", "id": "1"}
        
        Receive response:
        {"type": "response", "id": "1", "stdout": "hello\\n", "stderr": "", "exit_code": 0, ...}
    """
    # Validate token
    if not validate_token(token):
        logger.warning(f"Invalid token attempt: {token[:10]}...")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
    
    # Get device ID from token
    device_id = get_device_id(token)
    if not device_id:
        logger.error("Valid token but no device ID found")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication error")
        raise WebSocketException(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication error")
    
    logger.info(f"Authenticated device: {device_id}")
    
    # Handle WebSocket connection
    await handle_websocket(websocket, device_id)


def main():
    """
    Main entry point for running the server.
    
    Starts uvicorn server with configured settings.
    """
    uvicorn.run(
        "server.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,  # Set to True for development
        log_level=settings.log_level.lower()
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RemoteShell Manager Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "websocket": "/ws"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns:
        JSON response with server status
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "active_connections": len(manager.active_connections)
        }
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for client connections.
    
    Args:
        websocket: WebSocket connection from client
    """
    # Generate unique client ID
    client_id = str(uuid.uuid4())
    
    try:
        # Accept connection
        await manager.connect(websocket, client_id)
        
        # Send welcome message
        welcome_msg = {
            "type": "info",
            "message": f"Connected to RemoteShell Manager. Client ID: {client_id}",
            "client_id": client_id
        }
        await manager.send_message(websocket, welcome_msg)
        
        # Handle messages
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_text()
                
                # Process message
                await manager.handle_message(websocket, message, client_id)
                
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop for {client_id}: {str(e)}")
                break
    
    except Exception as e:
        logger.error(f"Error in WebSocket endpoint for {client_id}: {str(e)}")
    
    finally:
        # Clean up connection
        manager.disconnect(client_id)


def main():
    """Run the server."""
    import uvicorn
    
    logger.info("Starting RemoteShell Manager server on http://0.0.0.0:8000")
    logger.info("WebSocket endpoint: ws://localhost:8000/ws")
    logger.info("Health check: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
