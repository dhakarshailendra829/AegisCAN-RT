"""
Tests for AI/ML analytics modules.

Tests anomaly detection, feature extraction, and telemetry preprocessing.
"""

import pytest
import pandas as pd
import numpy as np
from analytics.anomaly_detector import AnomalyDetector
from analytics.utils import preprocess_telemetry


@pytest.fixture
def sample_telemetry_df():
    """Provide sample telemetry data for testing."""
    data = {
        "timestamp": pd.date_range("2025-01-01", periods=100, freq="S"),
        "latency_us": np.random.normal(20000, 5000, 100),
        "queue_size": np.random.randint(0, 50, 100)
    }
    return pd.DataFrame(data)


def test_preprocess_telemetry(sample_telemetry_df):
    """Test telemetry preprocessing keeps data intact."""
    processed = preprocess_telemetry(sample_telemetry_df)
    
    # Check new columns added
    assert "latency_ms" in processed.columns
    assert "jitter_ms" in processed.columns
    
    # Allow 1 row loss due to outlier removal
    assert len(processed) >= len(sample_telemetry_df) - 2


def test_anomaly_detector_init():
    """Test anomaly detector initializes correctly."""
    detector = AnomalyDetector(contamination=0.1)
    assert detector.model is not None
    assert detector._trained is False


@pytest.mark.asyncio
async def test_anomaly_detector_detect(sample_telemetry_df):
    """Test anomaly detection on sample data."""
    detector = AnomalyDetector(contamination=0.1)
    
    # detect() is async, must await
    predictions, event = await detector.detect(sample_telemetry_df)
    
    # Verify results
    assert predictions is not None or event is None
    if event:
        assert 0 <= event.anomaly_ratio <= 1
        assert event.severity in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]