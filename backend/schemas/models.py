# backend/schemas/models.py
from pydantic import BaseModel

class CANFrame(BaseModel):
    id: int
    data: bytes
    timestamp: float | None = None

class Telemetry(BaseModel):
    latency_ms: float
    jitter_ms: float
    attack_detected: bool = False