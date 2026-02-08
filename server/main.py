"""
FastAPI server with TLS support, security, database, and queue management.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import ssl
from pathlib import Path
import logging
from typing import Optional
import os

from config import Settings
from security import SecurityManager, SecurityPolicy
from database import Database
from queue_manager import QueueManager
from auth import AuthManager
from websocket_handler import ConnectionManager, WebSocketHandler
from shell_executor import ShellExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
RemoteShell Manager - FastAPI Server
Main application entry point with API endpoints and WebSocket support
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import uuid
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Initialize settings
settings = Settings()

# Initialize security manager
security_policy = SecurityPolicy(
    enable_whitelist=settings.enable_command_whitelist,
    allowed_commands=settings.allowed_commands,
    blocked_commands=settings.blocked_commands,
    max_execution_time=settings.max_execution_time,
    max_command_length=settings.max_command_length,
    allow_shell_operators=settings.allow_shell_operators
)
security_manager = SecurityManager(security_policy)

# Initialize database
database = Database(db_path=os.getenv("DATABASE_PATH", "remoteshell.db"))

# Initialize auth manager
auth_manager = AuthManager()

# Initialize queue manager
queue_manager = QueueManager(database)

# Initialize connection manager
connection_manager = ConnectionManager()

# Initialize WebSocket handler
websocket_handler = WebSocketHandler(
    connection_manager=connection_manager,
    security_manager=security_manager,
    database=database,
    queue_manager=queue_manager,
    auth_manager=auth_manager
)

# Initialize shell executor (for server-side operations)
shell_executor = ShellExecutor()

# Create FastAPI app
app = FastAPI(title="RemoteShell Manager Server")
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
    version="1.0.0"
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web interface (if directory exists)
static_path = Path("static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await database.connect()
    logger.info("Server startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await database.close()
    logger.info("Server shutdown complete")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "version": "1.0.0",
        "security": {
            "tls_enabled": settings.use_tls,
            "whitelist_enabled": settings.enable_command_whitelist,
            "max_execution_time": settings.max_execution_time
        },
        "connections": connection_manager.get_connection_count()
    }


@app.get("/api/devices")
async def list_devices():
    """
    List all registered devices.
    
    Returns:
        List of devices with status
    """
    devices = await database.list_devices()
    
    # Add online status from connection manager
    for device in devices:
        device_id = device.get("device_id")
        device["is_online"] = connection_manager.is_connected(device_id)
    
    return {"devices": devices}


@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """
    Get device information.
    
    Args:
        device_id: Device identifier
        
    Returns:
        Device details
    """
    device = await database.get_device(device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device["is_online"] = connection_manager.is_connected(device_id)
    return device


@app.post("/api/devices/{device_id}/command")
async def send_command(
    device_id: str,
    command: str = Query(..., description="Command to execute"),
    timeout: Optional[int] = Query(None, description="Execution timeout")
):
    """
    Send command to device.
    
    Args:
        device_id: Target device identifier
        command: Command to execute
        timeout: Optional timeout override
        
    Returns:
        Command status
    """
    # Validate command
    is_valid, error_msg = security_manager.validate_command(command, device_id)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Get effective timeout
    effective_timeout = security_manager.get_max_execution_time(timeout)
    
    # Check if device is online
    if connection_manager.is_connected(device_id):
        # Send command directly
        success = await connection_manager.send_message(device_id, {
            "type": "command",
            "command": command,
            "timeout": effective_timeout
        })
        
        if success:
            # Add to history as pending
            cmd_id = await database.add_command_history(
                device_id=device_id,
                command=command,
                status="sent"
            )
            
            return {
                "status": "sent",
                "device_id": device_id,
                "command": command,
                "timeout": effective_timeout,
                "command_id": cmd_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send command")
    else:
        # Queue command for offline device
        queue_id = await queue_manager.queue_command_for_device(
            device_id=device_id,
            command=command,
            timeout=effective_timeout
        )
        
        if queue_id:
            return {
                "status": "queued",
                "device_id": device_id,
                "command": command,
                "timeout": effective_timeout,
                "queue_id": queue_id,
                "message": "Device offline - command queued"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to queue command")


@app.get("/api/devices/{device_id}/history")
async def get_command_history(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get command history for device.
    
    Args:
        device_id: Device identifier
        limit: Maximum number of records
        offset: Pagination offset
        
    Returns:
        Command history
    """
    history = await database.get_command_history(
        device_id=device_id,
        limit=limit,
        offset=offset
    )
    
    return {
        "device_id": device_id,
        "history": history,
        "limit": limit,
        "offset": offset
    }
# Data models
class CommandRequest(BaseModel):
    device_id: str
    command: str
    timeout: int = 30

class CommandResponse(BaseModel):
    command_id: str
    device_id: str
    command: str
    status: str
    created_at: str

class CommandStatus(BaseModel):
    command_id: str
    device_id: str
    command: str
    status: str
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    execution_time: Optional[float] = None
    created_at: str
    completed_at: Optional[str] = None

class Device(BaseModel):
    device_id: str
    status: str
    queue_size: int = 0
    last_seen: Optional[str] = None

# In-memory storage (for demonstration)
devices: Dict[str, Device] = {}
commands: Dict[str, CommandStatus] = {}
command_history: List[CommandStatus] = []
websocket_connections: List[WebSocket] = []

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Root endpoint - serve index.html
@app.get("/")
async def root():
    """Serve the main HTML page"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "RemoteShell Manager API", "status": "running"}

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "devices": len(devices),
        "connections": len(websocket_connections)
    }

# API Endpoints

@app.get("/api/devices", response_model=List[Device])
async def get_devices():
    """Get list of all devices"""
    return list(devices.values())

@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """Get specific device information"""
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    return devices[device_id]

@app.post("/api/command", response_model=CommandResponse)
async def send_command(request: CommandRequest):
    """Send command to a device"""
    # Check if device exists
    if request.device_id not in devices:
        raise HTTPException(status_code=404, detail=f"Device '{request.device_id}' not found")
    
    # Check if device is online
    device = devices[request.device_id]
    if device.status != "online":
        raise HTTPException(status_code=400, detail=f"Device '{request.device_id}' is not online")
    
    # Create command
    command_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    command = CommandStatus(
        command_id=command_id,
        device_id=request.device_id,
        command=request.command,
        status="pending",
        created_at=now
    )
    
    commands[command_id] = command
    command_history.insert(0, command)
    
    # Keep history limited to 100 items
    if len(command_history) > 100:
        command_history.pop()
    
    logger.info(f"Command created: {command_id} for device {request.device_id}")
    
    # Simulate command execution (in real implementation, this would be sent via WebSocket to device)
    asyncio.create_task(simulate_command_execution(command_id, request.timeout))
    
    return CommandResponse(
        command_id=command_id,
        device_id=request.device_id,
        command=request.command,
        status="pending",
        created_at=now
    )

@app.get("/api/command/{command_id}", response_model=CommandStatus)
async def get_command_status(command_id: str):
    """Get command execution status and results"""
    if command_id not in commands:
        raise HTTPException(status_code=404, detail="Command not found")
    return commands[command_id]

@app.get("/api/history", response_model=List[CommandStatus])
async def get_history(
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get command history with optional filters"""
    filtered_history = command_history
    
    if device_id:
        filtered_history = [cmd for cmd in filtered_history if cmd.device_id == device_id]
    
    if status:
        filtered_history = [cmd for cmd in filtered_history if cmd.status == status]
    
    return filtered_history[:limit]

@app.get("/api/devices/{device_id}/history", response_model=List[CommandStatus])
async def get_device_history(device_id: str, limit: int = 50):
    """Get command history for a specific device"""
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device_history = [cmd for cmd in command_history if cmd.device_id == device_id]
    return device_history[:limit]

@app.get("/api/statistics")
async def get_statistics():
    """Get system statistics"""
    total_devices = len(devices)
    online_devices = sum(1 for d in devices.values() if d.status == "online")
    total_commands = len(command_history)
    
    status_counts = {}
    for cmd in command_history:
        status_counts[cmd.status] = status_counts.get(cmd.status, 0) + 1
    
    return {
        "devices": {
            "total": total_devices,
            "online": online_devices,
            "offline": total_devices - online_devices
        },
        "commands": {
            "total": total_commands,
            "by_status": status_counts
        }
    }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total connections: {len(websocket_connections)}")
    
    try:
        # Send initial device list
        await websocket.send_json({
            "type": "device_list",
            "devices": [device.dict() for device in devices.values()]
        })
        
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
            
            # Echo back or process the message
            await websocket.send_json({
                "type": "ack",
                "message": "Message received"
            })
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Remaining connections: {len(websocket_connections)}")

# Broadcast message to all connected WebSocket clients
async def broadcast_message(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients"""
    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket client: {e}")
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for websocket in disconnected:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# Simulate command execution (for demonstration)
async def simulate_command_execution(command_id: str, timeout: int):
    """Simulate command execution with random results"""
    import random
    
    # Wait a bit to simulate execution
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    command = commands[command_id]
    
    # Update command status
    command.status = "executing"
    await broadcast_message({
        "type": "command_update",
        "command_id": command_id,
        "status": "executing"
    })
    
    # Wait for execution
    execution_time = random.uniform(0.1, 1.5)
    await asyncio.sleep(execution_time)
    
    # Generate fake results
    success = random.random() > 0.2  # 80% success rate
    
    command.status = "completed" if success else "failed"
    command.exit_code = 0 if success else random.randint(1, 255)
    command.execution_time = execution_time
    command.completed_at = datetime.utcnow().isoformat()
    
    if success:
        # Simulate output based on common commands
        if "ls" in command.command:
            command.stdout = "file1.txt\nfile2.txt\ndirectory1\ndirectory2"
        elif "pwd" in command.command:
            command.stdout = "/home/user"
        elif "whoami" in command.command:
            command.stdout = "user"
        elif "date" in command.command:
            command.stdout = datetime.utcnow().strftime("%a %b %d %H:%M:%S UTC %Y")
        else:
            command.stdout = f"Command '{command.command}' executed successfully"
        command.stderr = ""
    else:
        command.stdout = ""
        command.stderr = f"Error executing command: {command.command}"
    
    # Update history
    for i, cmd in enumerate(command_history):
        if cmd.command_id == command_id:
            command_history[i] = command
            break
    
    # Broadcast update
    await broadcast_message({
        "type": "command_update",
        "command_id": command_id,
        "status": command.status,
        "exit_code": command.exit_code
    })
    
    logger.info(f"Command {command_id} completed with status: {command.status}")

# Initialize with some demo devices
@app.on_event("startup")
async def startup_event():
    """Initialize demo data on startup"""
    logger.info("Starting RemoteShell Manager...")
    
    # Add demo devices
    demo_devices = [
        Device(device_id="device1", status="online", queue_size=0, last_seen=datetime.utcnow().isoformat()),
        Device(device_id="device2", status="offline", queue_size=2, last_seen=datetime.utcnow().isoformat()),
        Device(device_id="device3", status="online", queue_size=0, last_seen=datetime.utcnow().isoformat()),
    ]
    
    for device in demo_devices:
        devices[device.device_id] = device
    
    logger.info(f"Initialized {len(demo_devices)} demo devices")
    logger.info("RemoteShell Manager started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
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
    Get queued commands for device.
    Get device queue status.
    
    Args:
        device_id: Device identifier
        
    Returns:
        Queue status
    """
    return await queue_manager.get_queue_status(device_id)


@app.get("/api/history")
async def get_all_history(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get command history for all devices.
    
    Args:
        limit: Maximum number of records
        offset: Pagination offset
        
    Returns:
        Command history
    """
    history = await database.get_command_history(
        device_id=None,
        limit=limit,
        offset=offset
    )
    
    return {
        "history": history,
        "limit": limit,
        "offset": offset
    }


@app.get("/web")
async def web_interface():
    """
    Serve web interface.
    
    Returns:
        HTML page
    """
    html_file = Path("static/index.html")
    
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text())
    else:
        return HTMLResponse(content="""
        <html>
        <head><title>RemoteShell Manager</title></head>
        <body>
        <h1>RemoteShell Manager</h1>
        <p>Web interface not installed.</p>
        <p>API is available at <a href="/docs">/docs</a></p>
        </body>
        </html>
        """)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """
    WebSocket endpoint for device connections.
    
    Args:
        websocket: WebSocket connection
        token: Authentication token (query parameter)
    """
    await websocket_handler.handle_connection(websocket, token)


def create_ssl_context() -> Optional[ssl.SSLContext]:
    """
    Create SSL context for TLS encryption.
    
    Returns:
        SSL context if TLS is enabled, None otherwise
    """
    if not settings.use_tls:
        return None
    
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    
    cert_path = Path(settings.tls_cert_path)
    key_path = Path(settings.tls_key_path)
    
    if not cert_path.exists() or not key_path.exists():
        logger.error("TLS certificate or key not found")
        raise FileNotFoundError("TLS certificate files missing")
    
    ssl_context.load_cert_chain(
        certfile=str(cert_path),
        keyfile=str(key_path)
    )
    
    # Set secure TLS parameters
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    
    logger.info("TLS enabled")
    return ssl_context


if __name__ == "__main__":
    # Log startup configuration
    logger.info("="*50)
    logger.info("RemoteShell Manager Server Starting")
    logger.info("="*50)
    logger.info(f"Host: {settings.host}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"TLS Enabled: {settings.use_tls}")
    logger.info(f"Command Whitelist: {settings.enable_command_whitelist}")
    logger.info(f"Max Execution Time: {settings.max_execution_time}s")
    logger.info("="*50)
    
    # Check if running as root (warning)
    import os
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        logger.warning("⚠️  WARNING: Running as root is not recommended!")
        logger.warning(f"⚠️  Consider running as user '{settings.run_as_user}'")
    
    # Start server
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        ssl_keyfile=settings.tls_key_path if settings.use_tls else None,
        ssl_certfile=settings.tls_cert_path if settings.use_tls else None,
        log_level=settings.log_level.lower()
    )
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
