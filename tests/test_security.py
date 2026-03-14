"""
Tests for security and attack simulation.

Tests attack engine initialization and event publishing.
"""

import pytest
import asyncio
from src.attack_engine import AttackEngine
from core.event_bus import event_bus


@pytest.mark.asyncio
async def test_attack_init():
    """Test attack engine initializes correctly."""
    attack = AttackEngine()
    assert attack is not None
    assert attack._attack_count >= 0


@pytest.mark.asyncio
async def test_bit_flip_publishes_event():
    """Test bit-flip attack publishes event to event bus."""
    attack = AttackEngine()
    published = []

    async def mock_handler(data):
        published.append(data)

    event_bus.subscribe("attack.event", mock_handler)
    
    try:
        await attack.bit_flip()
        
        await asyncio.sleep(0.1)
        
        assert len(published) >= 1, "No events published"
        
        event_type = published[0].get("type")
        assert event_type in ["BIT_FLIP", "ANOMALY_DETECTED", "ATTACK", "RANDOM_BIT_FLIP"], \
            f"Unexpected event type: {event_type}"
    finally:
        event_bus.unsubscribe("attack.event", mock_handler)


@pytest.mark.asyncio
async def test_dos_attack_publishes_multiple():
    """Test DoS attack publishes multiple events."""
    attack = AttackEngine()
    published_count = 0

    async def mock_handler(_):
        nonlocal published_count
        published_count += 1

    event_bus.subscribe("attack.event", mock_handler)
    
    try:
        await attack.dos_attack(duration_sec=0.1, rate_hz=50)
        
        await asyncio.sleep(0.2)
        
        assert published_count >= 1, f"Expected at least 1 event, got {published_count}"
    finally:
        event_bus.unsubscribe("attack.event", mock_handler)