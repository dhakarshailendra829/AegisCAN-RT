import pytest
import pandas as pd
import numpy as np
from analytics.anomaly_detector import AnomalyDetector
from analytics.utils import preprocess_telemetry

@pytest.fixture
def sample_telemetry_df():
    data = {
        "timestamp": pd.date_range("2025-01-01", periods=100, freq="S"),
        "latency_us": np.random.normal(20000, 5000, 100),
        "queue_size": np.random.randint(0, 50, 100)
    }
    return pd.DataFrame(data)

def test_preprocess_telemetry(sample_telemetry_df):
    processed = preprocess_telemetry(sample_telemetry_df)
    assert "latency_ms" in processed.columns
    assert "jitter_ms" in processed.columns
    assert len(processed) == len(sample_telemetry_df)

def test_anomaly_detector_init():
    detector = AnomalyDetector(contamination=0.1)
    assert detector.model is not None

def test_anomaly_detector_detect(sample_telemetry_df):
    detector = AnomalyDetector(contamination=0.1)
    predictions, ratio = detector.detect(sample_telemetry_df)
    assert len(predictions) > 0
    assert 0 <= ratio <= 1