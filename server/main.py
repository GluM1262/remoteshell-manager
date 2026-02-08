"""
FastAPI server with TLS support and security manager.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import ssl
from pathlib import Path
import logging
from typing import Optional

from config import Settings
from security import SecurityManager, SecurityPolicy

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

# Store active connections
active_connections: dict = {}


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
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for device connections.
    
    Args:
        websocket: WebSocket connection
        token: Authentication token (query parameter)
    """
    await websocket.accept()
    
    # Basic token validation (simplified for this implementation)
    if not token:
        await websocket.send_json({
            "type": "error",
            "message": "Authentication token required"
        })
        await websocket.close()
        return
    
    device_id = f"device_{token[:8]}"
    active_connections[device_id] = websocket
    
    logger.info(f"Device connected: {device_id}")
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "device_id": device_id,
            "message": "Connected to RemoteShell Manager"
        })
        
        # Handle incoming messages
        async for message in websocket.iter_json():
            if message.get("type") == "command":
                command = message.get("command", "")
                
                # Validate command
                is_valid, error_msg = security_manager.validate_command(
                    command, 
                    device_id=device_id
                )
                
                if not is_valid:
                    await websocket.send_json({
                        "type": "error",
                        "message": error_msg
                    })
                    continue
                
                # Get effective timeout
                timeout = security_manager.get_max_execution_time(
                    message.get("timeout")
                )
                
                logger.info(f"Command from {device_id}: {command} (timeout: {timeout}s)")
                
                # Send command execution acknowledgment
                # In a real implementation, this would execute the command
                await websocket.send_json({
                    "type": "command_queued",
                    "command": command,
                    "timeout": timeout,
                    "message": "Command queued for execution"
                })
            
            elif message.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": message.get("timestamp")
                })
    
    except WebSocketDisconnect:
        logger.info(f"Device disconnected: {device_id}")
    except Exception as e:
        logger.error(f"Error handling device {device_id}: {e}")
    finally:
        if device_id in active_connections:
            del active_connections[device_id]


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
