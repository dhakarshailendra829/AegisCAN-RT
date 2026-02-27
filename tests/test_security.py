import pytest
from src.attack_engine import AttackEngine

@pytest.mark.asyncio
async def test_attack_init():
    attack = AttackEngine()
    assert attack is not None

@pytest.mark.asyncio
async def test_bit_flip_publishes_event():
    attack = AttackEngine()
    published = []

    async def mock_handler(data):
        published.append(data)

    attack.bus.subscribe("attack.event", mock_handler)
    await attack.bit_flip()

    assert len(published) == 1
    assert published[0]["type"] == "BIT_FLIP"

@pytest.mark.asyncio
async def test_dos_attack_publishes_multiple():
    attack = AttackEngine()
    published_count = 0

    async def mock_handler(_):
        nonlocal published_count
        published_count += 1

    attack.bus.subscribe("attack.event", mock_handler)
    await attack.dos_attack(duration_sec=0.1, rate_hz=50)  

    assert published_count > 2  