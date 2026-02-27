# backend/routers/gateway.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.gateway import Gateway

router = APIRouter()

# Single global instance
gateway = Gateway()

class StatusResponse(BaseModel):
    status: str
    message: str

class AttackResponse(BaseModel):
    status: str
    message: str


@router.get("/status", response_model=StatusResponse)
async def gateway_status():
    is_running = getattr(gateway, "running", False)
    return StatusResponse(
        status="active" if is_running else "inactive",
        message="BLE-CAN gateway ready" if is_running else "Gateway not started"
    )


@router.post("/start", response_model=StatusResponse)
async def start_gateway():
    if getattr(gateway, "running", False):
        return StatusResponse(status="already_running", message="Gateway is already active")
    
    try:
        await gateway.start()
        return StatusResponse(status="started", message="Gateway deployed successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Start failed: {str(e)}")


@router.post("/stop", response_model=StatusResponse)
async def stop_gateway():
    if not getattr(gateway, "running", False):
        return StatusResponse(status="already_stopped", message="Gateway is not running")
    
    try:
        await gateway.stop()
        return StatusResponse(status="stopped", message="Gateway stopped successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stop failed: {str(e)}")

@router.post("/attack/{mode}")
async def trigger_attack(mode: str | None = None):  # Allow None
    if mode is None or mode.lower() == "none":
        gateway.set_attack_mode(None)
        return {"status": "success", "message": "Attack mode deactivated"}

    valid_modes = ["dos", "flip", "heart"]
    if mode not in valid_modes:
        raise HTTPException(status_code=422, detail=f"Invalid mode. Allowed: {', '.join(valid_modes)} or 'none'")

    gateway.set_attack_mode(mode)
    return {"status": "success", "message": f"Attack mode '{mode}' activated"}