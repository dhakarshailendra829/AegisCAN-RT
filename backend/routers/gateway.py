"""
Gateway API router for BLE-CAN gateway management and attack control.

Provides:
- Gateway lifecycle management (start/stop/status)
- Attack mode control with validation
- Health monitoring
- Reset functionality
"""

import logging
import time
from typing import Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.gateway import Gateway
from backend.schemas.models import (
    StatusResponse,
    AttackResponse,
    HealthResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()
gateway = Gateway()

# Track gateway start time for uptime calculation
_gateway_start_time: Optional[float] = None


# ============================================================================
# Enums
# ============================================================================

class AttackMode(str, Enum):
    """Valid attack modes for the gateway."""
    DOS = "dos"
    BIT_FLIP = "flip"
    HEARTBEAT_DROP = "heart"
    NONE = "none"


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Get gateway status",
    responses={
        200: {"description": "Status retrieved successfully"},
        500: {"description": "Failed to retrieve status"}
    }
)
async def gateway_status():
    """
    Get the current operational status of the BLE-CAN gateway.

    Returns:
        StatusResponse: Current gateway status (active/inactive)
    """
    try:
        is_running = getattr(gateway, "running", False)
        status_val = "active" if is_running else "inactive"
        message = "BLE-CAN gateway ready" if is_running else "Gateway not started"

        logger.debug(f"Status check: {status_val}")

        return StatusResponse(status=status_val, message=message)

    except Exception as e:
        logger.error(f"Failed to retrieve gateway status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve gateway status"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Get detailed gateway health",
    responses={
        200: {"description": "Health check successful"},
        500: {"description": "Health check failed"}
    }
)
async def gateway_health():
    """
    Get comprehensive health information about the gateway.

    Includes:
    - Running status
    - Attack mode status
    - Telemetry buffer status
    - Uptime calculation

    Returns:
        HealthResponse: Detailed health information
    """
    try:
        is_running = getattr(gateway, "running", False)
        attack_mode = getattr(gateway.can, "attack_mode", None) if hasattr(gateway, "can") else None
        telemetry_count = len(getattr(gateway, "telemetry", []))

        uptime = None
        if is_running and _gateway_start_time:
            uptime = time.time() - _gateway_start_time

        return HealthResponse(
            is_running=is_running,
            status="active" if is_running else "inactive",
            message="BLE-CAN gateway ready" if is_running else "Gateway not started",
            current_attack_mode=attack_mode,
            telemetry_count=telemetry_count,
            uptime_seconds=uptime
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.post(
    "/start",
    response_model=StatusResponse,
    summary="Start the gateway",
    responses={
        200: {"description": "Gateway started successfully"},
        409: {"description": "Gateway already running"},
        500: {"description": "Startup failed"}
    }
)
async def start_gateway():
    """
    Start the BLE-CAN gateway and initialize all components.

    Initializes:
    - BLE receiver
    - CAN translator
    - Attack engine
    - Event subscriptions
    - Database tables

    Returns:
        StatusResponse: Startup status

    Raises:
        HTTPException: If gateway already running or startup fails
    """
    global _gateway_start_time

    try:
        is_running = getattr(gateway, "running", False)

        if is_running:
            logger.warning("Start requested but gateway already running")
            return StatusResponse(
                status="already_running",
                message="Gateway is already active"
            )

        logger.info("Starting gateway...")
        _gateway_start_time = time.time()
        await gateway.start()

        logger.info("Gateway started successfully")
        return StatusResponse(
            status="started",
            message="Gateway deployed successfully"
        )

    except Exception as e:
        logger.error(f"Failed to start gateway: {e}", exc_info=True)
        _gateway_start_time = None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Start failed: {str(e)}"
        )


@router.post(
    "/stop",
    response_model=StatusResponse,
    summary="Stop the gateway",
    responses={
        200: {"description": "Gateway stopped successfully"},
        409: {"description": "Gateway not running"},
        500: {"description": "Shutdown failed"}
    }
)
async def stop_gateway():
    """
    Gracefully stop the BLE-CAN gateway and cleanup resources.

    Cleans up:
    - BLE receiver tasks
    - CAN bus interface
    - Attack simulation tasks
    - Database connections

    Returns:
        StatusResponse: Shutdown status

    Raises:
        HTTPException: If gateway not running or shutdown fails
    """
    global _gateway_start_time

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
        _gateway_start_time = None

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


@router.post(
    "/attack/{mode}",
    response_model=AttackResponse,
    summary="Activate or deactivate attack mode",
    responses={
        200: {"description": "Attack mode updated successfully"},
        422: {"description": "Invalid attack mode"},
        500: {"description": "Failed to set attack mode"}
    }
)
async def trigger_attack(mode: str):
    """
    Activate or deactivate attack simulation modes.

    Attack Modes:
    - **dos**: Denial of Service attack (80 Hz, 3 seconds)
    - **flip**: Bit flip attack (invert steering angle)
    - **heart**: Heartbeat drop attack (drop messages)
    - **none**: Deactivate all attacks

    Args:
        mode: Attack mode name

    Returns:
        AttackResponse: Confirmation of attack mode change

    Raises:
        HTTPException 422: Invalid mode
        HTTPException 500: Activation failed
    """
    try:
        # Normalize and validate mode
        mode_lower = mode.lower() if mode else ""
        valid_modes = [e.value for e in AttackMode]

        if mode_lower not in valid_modes:
            logger.warning(f"Invalid attack mode requested: {mode}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid mode '{mode}'. Allowed: dos, flip, heart, or none"
            )

        # Deactivate if mode is 'none'
        if mode_lower == AttackMode.NONE.value:
            logger.info("Deactivating attack mode")
            gateway.set_attack_mode(None)
            return AttackResponse(
                status="success",
                message="Attack mode deactivated",
                mode=None
            )

        # Activate attack mode
        logger.warning(f"Activating attack mode: {mode_lower}")
        gateway.set_attack_mode(mode_lower)

        return AttackResponse(
            status="success",
            message=f"Attack mode '{mode_lower}' activated",
            mode=mode_lower
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions

    except Exception as e:
        logger.error(f"Failed to set attack mode '{mode}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate attack mode: {str(e)}"
        )


@router.post(
    "/reset",
    response_model=StatusResponse,
    summary="Reset gateway state",
    responses={
        200: {"description": "Reset successful"},
        500: {"description": "Reset failed"}
    }
)
async def reset_gateway():
    """
    Reset the gateway to initial state.

    Operations:
    - Stops gateway if running
    - Clears attack modes
    - Preserves telemetry data
    - Clears all running tasks

    Returns:
        StatusResponse: Reset status
    """
    global _gateway_start_time

    try:
        logger.info("Resetting gateway...")

        is_running = getattr(gateway, "running", False)
        if is_running:
            await gateway.stop()

        # Reset attack mode
        gateway.set_attack_mode(None)
        _gateway_start_time = None

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