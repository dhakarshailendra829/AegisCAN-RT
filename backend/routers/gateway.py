"""
Gateway API router for BLE-CAN gateway management and attack control.

Provides endpoints for:
- Gateway lifecycle management (start/stop/status)
- Attack mode control with validation
"""

import logging
from enum import Enum
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.gateway import Gateway

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter()
gateway = Gateway()


# ============================================================================
# Enums for Type Safety
# ============================================================================

class AttackMode(str, Enum):
    """Valid attack modes for the gateway."""
    DOS = "dos"
    BIT_FLIP = "flip"
    HEARTBEAT_DROP = "heart"
    NONE = "none"


# ============================================================================
# Pydantic Response Models
# ============================================================================

class StatusResponse(BaseModel):
    """Standard response model for gateway status operations."""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Human-readable status message")

    class Config:
        json_schema_extra = {
            "example": {"status": "active", "message": "BLE-CAN gateway ready"}
        }


class AttackResponse(BaseModel):
    """Response model for attack operations."""
    status: str = Field(..., description="Operation status (success/error)")
    message: str = Field(..., description="Operation details")
    mode: Optional[str] = Field(None, description="Active attack mode or None")

    class Config:
        json_schema_extra = {
            "example": {"status": "success", "message": "Attack mode 'dos' activated", "mode": "dos"}
        }


class HealthResponse(BaseModel):
    """Detailed gateway health and status information."""
    is_running: bool = Field(..., description="Whether gateway is currently running")
    status: str = Field(..., description="Current operational status")
    message: str = Field(..., description="Descriptive status message")
    current_attack_mode: Optional[str] = Field(None, description="Currently active attack mode")
    telemetry_count: int = Field(..., description="Number of telemetry entries buffered")

    class Config:
        json_schema_extra = {
            "example": {
                "is_running": True,
                "status": "active",
                "message": "BLE-CAN gateway ready",
                "current_attack_mode": None,
                "telemetry_count": 42
            }
        }


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/status", response_model=StatusResponse)
async def gateway_status():
    """
    Get the current status of the BLE-CAN gateway.

    Returns:
        StatusResponse: Current gateway status (active/inactive)
    """
    try:
        is_running = getattr(gateway, "running", False)
        return StatusResponse(
            status="active" if is_running else "inactive",
            message="BLE-CAN gateway ready" if is_running else "Gateway not started"
        )
    except Exception as e:
        logger.error(f"Failed to retrieve gateway status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve gateway status"
        )


@router.get("/health", response_model=HealthResponse)
async def gateway_health():
    """
    Get detailed health information about the gateway including telemetry buffer status.

    Returns:
        HealthResponse: Comprehensive gateway health information
    """
    try:
        is_running = getattr(gateway, "running", False)
        attack_mode = getattr(gateway.can, "attack_mode", None) if hasattr(gateway, "can") else None
        telemetry_count = len(getattr(gateway, "telemetry", []))

        return HealthResponse(
            is_running=is_running,
            status="active" if is_running else "inactive",
            message="BLE-CAN gateway ready" if is_running else "Gateway not started",
            current_attack_mode=attack_mode,
            telemetry_count=telemetry_count
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.post("/start", response_model=StatusResponse)
async def start_gateway():
    """
    Start the BLE-CAN gateway and initialize all components.

    Returns:
        StatusResponse: Startup status and message

    Raises:
        HTTPException: If gateway is already running or startup fails
    """
    try:
        is_running = getattr(gateway, "running", False)

        if is_running:
            logger.warning("Start requested but gateway already running")
            return StatusResponse(
                status="already_running",
                message="Gateway is already active"
            )

        logger.info("Starting gateway...")
        await gateway.start()

        logger.info("Gateway started successfully")
        return StatusResponse(
            status="started",
            message="Gateway deployed successfully"
        )

    except Exception as e:
        logger.error(f"Failed to start gateway: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Start failed: {str(e)}"
        )


@router.post("/stop", response_model=StatusResponse)
async def stop_gateway():
    """
    Gracefully stop the BLE-CAN gateway and cleanup resources.

    Returns:
        StatusResponse: Shutdown status and message

    Raises:
        HTTPException: If gateway is not running or shutdown fails
    """
    try:
        is_running = getattr(gateway, "running", False)

        if not is_running:
            logger.warning("Stop requested but gateway not running")
            return StatusResponse(
                status="already_stopped",
                message="Gateway is not running"
            )

        logger.info("Stopping gateway...")
        await gateway.stop()

        logger.info("Gateway stopped successfully")
        return StatusResponse(
            status="stopped",
            message="Gateway stopped successfully"
        )

    except Exception as e:
        logger.error(f"Failed to stop gateway: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stop failed: {str(e)}"
        )


@router.post("/attack/{mode}")
async def trigger_attack(mode: str | None = None):
    """
    Activate or deactivate attack simulation modes on the gateway.

    Attack Modes:
    - **dos**: Denial of Service attack simulation
    - **flip**: Bit flip attack simulation
    - **heart**: Heartbeat drop attack simulation
    - **none**: Deactivate all attacks

    Args:
        mode: Attack mode name (dos, flip, heart, or none)

    Returns:
        dict: Confirmation of attack mode change with status and message

    Raises:
        HTTPException 422: If mode is invalid
        HTTPException 500: If attack mode activation fails
    """
    try:
        # Normalize and validate mode
        mode_lower = mode.lower() if mode else ""
        valid_modes = [e.value for e in AttackMode]

        if mode_lower not in valid_modes:
            logger.warning(f"Invalid attack mode requested: {mode}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid mode. Allowed: {', '.join([m for m in valid_modes if m != 'none'])}, or 'none'"
            )

        # Deactivate if mode is 'none'
        if mode_lower == AttackMode.NONE.value:
            logger.info("Deactivating attack mode")
            gateway.set_attack_mode(None)
            return {
                "status": "success",
                "message": "Attack mode deactivated",
                "mode": None
            }

        # Activate attack mode
        logger.warning(f"Activating attack mode: {mode_lower}")
        gateway.set_attack_mode(mode_lower)

        return {
            "status": "success",
            "message": f"Attack mode '{mode_lower}' activated",
            "mode": mode_lower
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions

    except Exception as e:
        logger.error(f"Failed to set attack mode '{mode}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate attack mode: {str(e)}"
        )


@router.post("/reset", response_model=StatusResponse)
async def reset_gateway():
    """
    Reset the gateway to its initial state.

    This will:
    - Stop the gateway if running
    - Clear attack modes
    - Preserve telemetry data

    Returns:
        StatusResponse: Reset status and message
    """
    try:
        logger.info("Resetting gateway...")

        is_running = getattr(gateway, "running", False)
        if is_running:
            await gateway.stop()

        # Reset attack mode
        gateway.set_attack_mode(None)

        logger.info("Gateway reset successfully")
        return StatusResponse(
            status="success",
            message="Gateway reset to initial state"
        )

    except Exception as e:
        logger.error(f"Failed to reset gateway: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reset failed: {str(e)}"
        )