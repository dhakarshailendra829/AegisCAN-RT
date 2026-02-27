# tests/test_gateway.py
import pytest
import asyncio
from src.gateway import Gateway

@pytest.mark.asyncio
async def test_gateway_init(gateway):
    assert gateway.running is False
    assert gateway.ble is not None
    assert gateway.can is not None
    assert gateway.attack is not None
    assert len(gateway.telemetry) == 0

@pytest.mark.asyncio
async def test_gateway_start_stop(gateway):
    assert gateway.running is False

    await gateway.start()
    assert gateway.running is True

    await gateway.stop()
    assert gateway.running is False

@pytest.mark.asyncio
async def test_gateway_attack_mode(gateway):
    gateway.set_attack_mode("dos")
    assert gateway.can.attack_mode == "dos"

    gateway.set_attack_mode(None)
    assert gateway.can.attack_mode is None