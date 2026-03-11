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

logger = logging.getLogger(__name__)

router = APIRouter()
gateway = Gateway()

class AttackMode(str, Enum):
    DOS = "dos"
    BIT_FLIP = "flip"
    HEARTBEAT_DROP = "heart"
    NONE = "none"

class StatusResponse(BaseModel):
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Human-readable status message")

    class Config:
        json_schema_extra = {
            "example": {"status": "active", "message": "BLE-CAN gateway ready"}
        }

class AttackResponse(BaseModel):
    status: str = Field(..., description="Operation status (success/error)")
    message: str = Field(..., description="Operation details")
    mode: Optional[str] = Field(None, description="Active attack mode or None")

    class Config:
        json_schema_extra = {
            "example": {"status": "success", "message": "Attack mode 'dos' activated", "mode": "dos"}
        }

class HealthResponse(BaseModel):
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

@router.get("/status", response_model=StatusResponse)
async def gateway_status():
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
    try:
        mode_lower = mode.lower() if mode else ""
        valid_modes = [e.value for e in AttackMode]

        if mode_lower not in valid_modes:
            logger.warning(f"Invalid attack mode requested: {mode}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid mode. Allowed: {', '.join([m for m in valid_modes if m != 'none'])}, or 'none'"
            )

        if mode_lower == AttackMode.NONE.value:
            logger.info("Deactivating attack mode")
            gateway.set_attack_mode(None)
            return {
                "status": "success",
                "message": "Attack mode deactivated",
                "mode": None
            }

        logger.warning(f"Activating attack mode: {mode_lower}")
        gateway.set_attack_mode(mode_lower)

        return {
            "status": "success",
            "message": f"Attack mode '{mode_lower}' activated",
            "mode": mode_lower
        }

    except HTTPException:
        raise  

    except Exception as e:
        logger.error(f"Failed to set attack mode '{mode}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate attack mode: {str(e)}"
        )

@router.post("/reset", response_model=StatusResponse)
async def reset_gateway():
    try:
        logger.info("Resetting gateway...")

        is_running = getattr(gateway, "running", False)
        if is_running:
            await gateway.stop()

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