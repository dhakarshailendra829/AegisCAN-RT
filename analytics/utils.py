# analytics/utils.py
import pandas as pd
import numpy as np
from core.logger_engine import logger

def preprocess_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and prepare telemetry data for models."""
    try:
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', unit='s')
        df = df.dropna(subset=['latency_us', 'queue_size'])  # adjust columns
        df['latency_ms'] = df['latency_us'] / 1000
        df['jitter_ms'] = df['latency_ms'].diff().abs().fillna(0)
        return df
    except Exception as e:
        logger.error(f"Telemetry preprocessing failed: {e}")
        return pd.DataFrame()

def extract_features(df: pd.DataFrame) -> np.ndarray:
    """Extract model-ready features (example)."""
    if df.empty:
        return np.array([])
    features = df[['latency_ms', 'jitter_ms', 'queue_size']].values
    return features  # add rolling mean, std, etc. later