"""
Tests for data pipeline and steering angle conversion.
Tests CAN translator scaling and range validation.
"""

import pytest
from src.can_translator import CANTranslator

@pytest.fixture
def translator():
    return CANTranslator()

def test_scale_steering(translator):
    result = translator._scale_steering(127)
    assert -50 <= result <= 50, f"Center should be near 0, got {result}"
    
    result = translator._scale_steering(255)
    assert 400 <= result <= 1000, f"Max should be near 900, got {result}"
    
    result = translator._scale_steering(0)
    assert -1000 <= result <= -400, f"Min should be near -900, got {result}"

def test_scale_range(translator):
    result_0 = translator._scale_steering(0)
    assert result_0 < 0, f"Value 0 should be negative, got {result_0}"
    
    result_255 = translator._scale_steering(255)
    assert result_255 > 0, f"Value 255 should be positive, got {result_255}"
    
    result_127 = translator._scale_steering(127)
    assert -100 <= result_127 <= 100, f"Center should be near 0, got {result_127}"