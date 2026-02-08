"""
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

# Create FastAPI app
app = FastAPI(
    title="RemoteShell Manager",
    description="Remote Linux device management system via WebSocket",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
