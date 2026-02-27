import pytest
from src.gateway import Gateway
from core.event_bus import event_bus
from core.task_manager import task_manager

@pytest.fixture
def gateway():
    gw = Gateway()
    yield gw
    if gw.running:
        gw.stop()

@pytest.fixture
def mock_bus():
    return event_bus  