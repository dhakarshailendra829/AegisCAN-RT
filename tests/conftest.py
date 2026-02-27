import pytest
from src.gateway import Gateway
from core.event_bus import event_bus
from core.task_manager import task_manager

@pytest.fixture
def gateway():
    """Fresh gateway instance for each test"""
    gw = Gateway()
    yield gw
    # Cleanup after test
    if gw.running:
        gw.stop()

@pytest.fixture
def mock_bus():
    """Fresh event bus for isolation"""
    return event_bus  # or create new if needed