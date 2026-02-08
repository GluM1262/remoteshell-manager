"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SendCommandRequest(BaseModel):
    """Request to send command to device."""
    device_id: str = Field(..., description="Target device identifier")
    command: str = Field(..., description="Command to execute")
    timeout: Optional[int] = Field(30, description="Command timeout in seconds", ge=1, le=3600)
    priority: Optional[int] = Field(0, description="Command priority (higher = more important)", ge=0, le=10)


class CommandStatus(BaseModel):
    """Command status response."""
    command_id: str
    device_id: str
    command: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CommandResponse(BaseModel):
    """Response for command creation."""
    command_id: str
    status: str = "pending"
    message: Optional[str] = None


class DeviceStatus(BaseModel):
    """Device status information."""
    device_id: str
    status: str
    first_seen: datetime
    last_connected: datetime
    queue_size: int = 0
    total_commands: int = 0
    metadata: Optional[dict] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class DeviceRegistration(BaseModel):
    """Device registration request."""
    device_id: str
    device_token: str
    metadata: Optional[dict] = None


class HistoryQuery(BaseModel):
    """History query parameters."""
    device_id: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)


class Statistics(BaseModel):
    """Statistics response."""
    total_commands: int
    completed: int
    failed: int
    pending: int
    timeout: int = 0
    avg_execution_time: float


class CleanupRequest(BaseModel):
    """Cleanup request."""
    days: int = Field(30, description="Delete records older than this many days", ge=1, le=365)


class ExportRequest(BaseModel):
    """Export request."""
    format: str = Field("json", description="Export format (json or csv)")
    device_id: Optional[str] = None
    limit: int = Field(1000, ge=1, le=10000)


class BulkCommandRequest(BaseModel):
    """Request to send command to multiple devices."""
    device_ids: list[str] = Field(..., description="List of target device identifiers")
    command: str = Field(..., description="Command to execute")
    timeout: Optional[int] = Field(30, description="Command timeout in seconds", ge=1, le=3600)
    priority: Optional[int] = Field(0, description="Command priority", ge=0, le=10)


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""
    type: str
    command_id: Optional[str] = None
    command: Optional[str] = None
    timeout: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None


class AuthRequest(BaseModel):
    """Authentication request."""
    device_id: str
    device_token: str
"""
Pydantic Models

Defines data models for WebSocket messages and device information.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime, timezone


class CommandMessage(BaseModel):
    """
    Message from client requesting command execution.
    """
    type: Literal["command"]
    command: str = Field(..., min_length=1, max_length=10000)
    id: str = Field(..., min_length=1)
    timeout: Optional[int] = 30


class ResponseMessage(BaseModel):
    """
    Response message with command execution results.
    """
    type: Literal["response"]
    id: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorMessage(BaseModel):
    """
    Error message for invalid requests or execution failures.
    """
    type: Literal["error"]
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeviceInfo(BaseModel):
    """
    Information about a connected device.
    """
    device_id: str
    connected_at: datetime
    last_command: Optional[datetime] = None
