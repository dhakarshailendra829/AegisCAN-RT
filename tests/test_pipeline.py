import pytest
from src.can_translator import CANTranslator

@pytest.fixture
def translator():
    return CANTranslator()

def test_scale_steering(translator):
    assert translator.scale_steering(127) == 0
    assert translator.scale_steering(255) == 900
    assert translator.scale_steering(0) == -900

def test_scale_range(translator):
    assert translator.scale_steering(0) < 0
    assert translator.scale_steering(255) > 0
    assert translator.scale_steering(127) == 0