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


@app.get("/api/devices/{device_id}/queue")
async def get_device_queue(device_id: str):
    """
    Get queued commands for device.
    
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
    if os.geteuid() == 0:
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
