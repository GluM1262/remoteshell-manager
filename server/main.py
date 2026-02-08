"""FastAPI application for RemoteShell Manager server.

This module provides the main FastAPI application with WebSocket support
for remote shell command execution.
"""

import logging
import sys
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
    description="Remote Linux device management via WebSocket",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
