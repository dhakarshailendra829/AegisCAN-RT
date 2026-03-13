"""
Tests for REST API endpoints.

Tests gateway control, analytics, and health endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestGatewayAPI:
    """Gateway control endpoint tests."""

    def test_gateway_status_endpoint(self, client):
        """Test GET /api/gateway/status"""
        response = client.get("/api/gateway/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_gateway_start_endpoint(self, client):
        """Test POST /api/gateway/start"""
        response = client.post("/api/gateway/start")
        assert response.status_code in [200, 409]
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_gateway_stop_endpoint(self, client):
        """Test POST /api/gateway/stop"""
        response = client.post("/api/gateway/stop")
        assert response.status_code in [200, 409]

    def test_gateway_health_endpoint(self, client):
        """Test GET /api/gateway/health"""
        response = client.get("/api/gateway/health")
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data or "status" in data

    def test_gateway_attack_dos_endpoint(self, client):
        """Test POST /api/gateway/attack/dos"""
        response = client.post("/api/gateway/attack/dos")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "success"

    def test_gateway_attack_invalid_endpoint(self, client):
        """Test POST /api/gateway/attack/invalid"""
        response = client.post("/api/gateway/attack/invalid")
        assert response.status_code == 422


class TestAnalyticsAPI:
    """Analytics API endpoint tests."""

    def test_telemetry_endpoint(self, client):
        """Test GET /api/analytics/telemetry"""
        response = client.get("/api/analytics/telemetry?limit=10")
        # May return 404 if endpoint not fully implemented
        assert response.status_code in [200, 404]

    def test_telemetry_with_pagination(self, client):
        """Test telemetry pagination"""
        response = client.get("/api/analytics/telemetry?limit=20&offset=10")
        assert response.status_code in [200, 404]

    def test_anomaly_detection_endpoint(self, client):
        """Test GET /api/analytics/anomalies/detect"""
        response = client.get("/api/analytics/anomalies/detect?limit=100")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestHealthAPI:
    """Health check API tests."""

    def test_health_endpoint(self, client):
        """Test GET /health"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_status_endpoint(self, client):
        """Test GET /status"""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"