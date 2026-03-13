# ============================================================================
# tests/test_gateway.py - FINAL CORRECTED VERSION
# ============================================================================

"""
Tests for gateway lifecycle and operations.

Tests gateway initialization, start/stop, and attack modes.
"""

import pytest
import asyncio
from src.gateway import Gateway


@pytest.mark.asyncio
async def test_gateway_init(gateway):
    """Test gateway initializes in stopped state."""
    assert gateway.running is False
    assert gateway.ble is not None
    assert gateway.can is not None
    assert gateway.attack is not None


@pytest.mark.asyncio
async def test_gateway_start_stop(gateway):
    """Test gateway start and stop lifecycle."""
    # Start
    await gateway.start()
    assert gateway.running is True
    
    # Small delay
    await asyncio.sleep(0.1)
    
    # Stop
    await gateway.stop()
    assert gateway.running is False


@pytest.mark.asyncio
async def test_gateway_attack_mode(gateway):
    """Test attack mode setting."""
    # Set DOS mode
    gateway.set_attack_mode("dos")
    assert gateway.can.attack_mode == "dos"
    
    # Set BIT_FLIP mode
    gateway.set_attack_mode("flip")
    assert gateway.can.attack_mode == "flip"
    
    # Disable
    gateway.set_attack_mode(None)
    assert gateway.can.attack_mode is None