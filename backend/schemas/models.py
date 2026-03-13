"""
Pydantic models for API request/response validation.

Provides:
- Type-safe request/response models
- Validation rules
- Example data for documentation
"""

from typing import Optional, Any, Dict, List
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================

class GatewayStatusEnum(str, Enum):
    """Gateway operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ALREADY_RUNNING = "already_running"
    ALREADY_STOPPED = "already_stopped"


class AttackModeEnum(str, Enum):
    """Valid attack simulation modes."""
    DOS = "dos"
    BIT_FLIP = "flip"
    HEARTBEAT_DROP = "heart"
    NONE = "none"


class OperationStatusEnum(str, Enum):
    """Operation result status."""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


# ============================================================================
# Gateway Models
# ============================================================================

class StatusResponse(BaseModel):
    """Standard gateway status response."""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Human-readable message")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "active",
                "message": "BLE-CAN gateway ready"
            }
        }


class HealthResponse(BaseModel):
    """Detailed gateway health information."""
    is_running: bool = Field(..., description="Gateway running status")
    status: str = Field(..., description="Current operational status")
    message: str = Field(..., description="Status message")
    current_attack_mode: Optional[str] = Field(None, description="Active attack mode")
    telemetry_count: int = Field(..., description="Buffered telemetry entries")
    uptime_seconds: Optional[float] = Field(None, description="Gateway uptime in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "is_running": True,
                "status": "active",
                "message": "BLE-CAN gateway ready",
                "current_attack_mode": None,
                "telemetry_count": 42,
                "uptime_seconds": 3600.5
            }
        }


class AttackResponse(BaseModel):
    """Attack mode operation response."""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Operation message")
    mode: Optional[str] = Field(None, description="Active attack mode")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Attack mode 'dos' activated",
                "mode": "dos"
            }
        }


# ============================================================================
# CAN Models
# ============================================================================

class CANFrame(BaseModel):
    """CAN bus frame model."""
    arbitration_id: int = Field(..., description="CAN ID", ge=0, le=0x7FF)
    data: bytes = Field(..., description="Frame data", min_length=0, max_length=8)
    timestamp: Optional[float] = Field(None, description="Frame timestamp")
    is_extended_id: bool = Field(False, description="Use extended CAN ID")

    @field_validator("data")
    @classmethod
    def validate_data_length(cls, v):
        """CAN frames must be 0-8 bytes."""
        if len(v) > 8:
            raise ValueError("CAN frame data must be 0-8 bytes")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "arbitration_id": 256,
                "data": b"\x00\x01\x02\x03\x04\x05\x06\x07",
                "timestamp": 1234567890.123,
                "is_extended_id": False
            }
        }


# ============================================================================
# Telemetry Models
# ============================================================================

class TelemetryEntry(BaseModel):
    """Single telemetry data entry."""
    type: str = Field(..., description="Entry type (CAN_TX, ATTACK, etc)")
    angle: Optional[float] = Field(None, description="Steering angle in degrees")
    latency_us: Optional[int] = Field(None, description="Message latency in microseconds")
    queue_size: Optional[int] = Field(None, description="Queue size at time of event")
    priority: Optional[int] = Field(None, description="Message priority level")
    timestamp_us: Optional[int] = Field(None, description="Timestamp in microseconds")
    extra: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "CAN_TX",
                "angle": 45.5,
                "latency_us": 125,
                "queue_size": 3,
                "priority": 1,
                "timestamp_us": 1234567890123,
                "extra": {"source": "BLE"}
            }
        }


class TelemetryResponse(BaseModel):
    """Telemetry data response."""
    count: int = Field(..., description="Number of entries returned")
    entries: List[TelemetryEntry] = Field(..., description="Telemetry entries")
    has_more: bool = Field(False, description="More data available")

    class Config:
        json_schema_extra = {
            "example": {
                "count": 10,
                "entries": [],
                "has_more": False
            }
        }


class Telemetry(BaseModel):
    """Telemetry metrics model."""
    latency_ms: float = Field(..., description="Latency in milliseconds")
    jitter_ms: float = Field(..., description="Jitter in milliseconds")
    attack_detected: bool = Field(False, description="Attack detected flag")

    class Config:
        json_schema_extra = {
            "example": {
                "latency_ms": 0.125,
                "jitter_ms": 0.012,
                "attack_detected": False
            }
        }

class ErrorResponse(BaseModel):
    """Standard error response."""
    status: str = Field(default="error", description="Error status")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    error_code: Optional[str] = Field(None, description="Error code for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Failed to start gateway",
                "detail": "Gateway already running",
                "error_code": "GATEWAY_ALREADY_RUNNING"
            }
        }