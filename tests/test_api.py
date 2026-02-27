# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_gateway_start():
    response = client.post("/api/gateway/start")
    assert response.status_code in (200, 202)  # 200 or already running
    assert "started" in response.json()["status"] or "already" in response.json()["status"]

def test_telemetry_endpoint():
    response = client.get("/api/analytics/telemetry?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # array of dicts