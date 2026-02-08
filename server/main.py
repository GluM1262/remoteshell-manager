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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    logger.info("Shutting down RemoteShell Manager Server")


# Initialize FastAPI application
app = FastAPI(
    title="RemoteShell Manager",
    description="WebSocket-based remote shell command execution server",
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
    )


if __name__ == "__main__":
    main()
