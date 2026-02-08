"""
Pydantic Models

Defines data models for WebSocket messages and device information.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


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
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorMessage(BaseModel):
    """
    Error message for invalid requests or execution failures.
    """
    type: Literal["error"]
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DeviceInfo(BaseModel):
    """
    Information about a connected device.
    """
    device_id: str
    connected_at: datetime
    last_command: Optional[datetime] = None
