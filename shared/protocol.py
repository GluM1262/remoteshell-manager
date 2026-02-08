"""Data exchange protocol for RemoteShell Manager.

This module defines the message types and data models used for communication
between the client and server over WebSocket connections.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Enumeration of message types."""
    
    COMMAND = "command"
    RESPONSE = "response"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class CommandMessage(BaseModel):
    """Message for sending a command from client to server.
    
    Attributes:
        type: Message type (always "command")
        command: The shell command to execute
        timestamp: Time when the command was sent
    """
    
    type: MessageType = Field(default=MessageType.COMMAND)
    command: str = Field(..., min_length=1, description="Shell command to execute")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ResponseMessage(BaseModel):
    """Message for sending command execution results from server to client.
    
    Attributes:
        type: Message type (always "response")
        stdout: Standard output from command execution
        stderr: Standard error from command execution
        exit_code: Exit code of the command
        timestamp: Time when the response was sent
    """
    
    type: MessageType = Field(default=MessageType.RESPONSE)
    stdout: str = Field(default="")
    stderr: str = Field(default="")
    exit_code: int = Field(..., description="Exit code of the command")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorMessage(BaseModel):
    """Message for sending error information.
    
    Attributes:
        type: Message type (always "error")
        error: Error description
        timestamp: Time when the error occurred
    """
    
    type: MessageType = Field(default=MessageType.ERROR)
    error: str = Field(..., min_length=1, description="Error description")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PingMessage(BaseModel):
    """Ping message for connection health check.
    
    Attributes:
        type: Message type (always "ping")
        timestamp: Time when the ping was sent
    """
    
    type: MessageType = Field(default=MessageType.PING)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PongMessage(BaseModel):
    """Pong message in response to ping.
    
    Attributes:
        type: Message type (always "pong")
        timestamp: Time when the pong was sent
    """
    
    type: MessageType = Field(default=MessageType.PONG)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
