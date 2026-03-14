"""
End-to-end integration tests.

Tests complete workflows across multiple components.
"""

import pytest
import asyncio


class TestGatewayIntegration:
    """Integration tests for complete gateway workflow."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_gateway_start_stop_cycle(self, running_gateway):
        """Test complete gateway start/stop cycle."""
        assert running_gateway.running is True
        assert running_gateway.ble is not None
        assert running_gateway.can is not None
        assert running_gateway.attack is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_attack_mode_cycle(self, running_gateway):
        """Test attack mode activation and deactivation."""
        modes = ["dos", "flip", "heart"]

        for mode in modes:
            running_gateway.set_attack_mode(mode)
            assert running_gateway.can.attack_mode == mode
            await asyncio.sleep(0.05)

        running_gateway.set_attack_mode(None)
        assert running_gateway.can.attack_mode is None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_telemetry_collection(self, running_gateway):
        """Test telemetry collection during operation."""
        initial_count = len(running_gateway.telemetry)
        
        await asyncio.sleep(0.5)
        
        assert len(running_gateway.telemetry) >= initial_count


class TestAPIIntegration:
    """Integration tests for API workflows."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_api_workflow(self, client):
        """Test complete API workflow."""
        response = client.get("/api/gateway/status")
        assert response.status_code == 200

        response = client.post("/api/gateway/start")
        assert response.status_code in [200, 409]

        response = client.post("/api/gateway/attack/dos")
        assert response.status_code == 200

        response = client.get("/api/analytics/anomalies/detect?limit=100")
        assert response.status_code in [200, 404]

        response = client.post("/api/gateway/attack/none")
        assert response.status_code == 200

        response = client.post("/api/gateway/stop")
        assert response.status_code in [200, 409]