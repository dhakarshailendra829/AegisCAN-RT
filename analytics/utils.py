"""
Analytics utility functions for data preprocessing and feature extraction.

Features:
- Telemetry data cleaning
- Feature engineering
- Time series handling
- Data validation
"""

import logging
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FeatureVector:
    """Extracted features for ML models."""
    latency_ms: float
    jitter_ms: float
    queue_size: int
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    timestamp: Optional[float] = None

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for ML."""
        return np.array([
            self.latency_ms,
            self.jitter_ms,
            self.queue_size,
            self.cpu_percent or 0,
            self.memory_percent or 0,
            self.disk_percent or 0
        ])


def preprocess_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare telemetry data for analysis.

    Args:
        df: Raw telemetry DataFrame

    Returns:
        pd.DataFrame: Preprocessed telemetry data

    Raises:
        ValueError: If data is invalid
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for preprocessing")
        return pd.DataFrame()

    try:
        # Create copy to avoid modifying original
        df = df.copy()

        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(
                df['timestamp'],
                errors='coerce',
                utc=True
            )

        # Convert latency from microseconds to milliseconds
        if 'latency_us' in df.columns:
            df['latency_ms'] = df['latency_us'] / 1000.0

        # Calculate jitter (variation in latency)
        if 'latency_ms' in df.columns:
            df['jitter_ms'] = (
                df['latency_ms'].diff().abs().fillna(0)
            )

        # Drop rows with critical missing values
        required_cols = ['latency_ms', 'queue_size']
        if all(col in df.columns for col in required_cols):
            df = df.dropna(subset=required_cols)
        else:
            logger.warning(
                f"Missing required columns: {required_cols}. "
                f"Available: {list(df.columns)}"
            )

        # Remove outliers (z-score > 3)
        if 'latency_ms' in df.columns and len(df) > 1:
            z_scores = np.abs((df['latency_ms'] - df['latency_ms'].mean()) 
                             / df['latency_ms'].std())
            df = df[z_scores < 3.0]

        logger.debug(
            f"Preprocessed telemetry: {len(df)} samples, "
            f"columns={list(df.columns)}"
        )
        return df

    except Exception as e:
        logger.error(f"Telemetry preprocessing failed: {e}", exc_info=True)
        return pd.DataFrame()


def extract_features(
    df: pd.DataFrame,
    include_system_metrics: bool = False
) -> np.ndarray:
    """
    Extract ML-ready features from telemetry.

    Args:
        df: Preprocessed telemetry DataFrame
        include_system_metrics: Include CPU/memory/disk metrics

    Returns:
        np.ndarray: Feature matrix (n_samples, n_features)
    """
    if df.empty:
        logger.warning("Cannot extract features from empty DataFrame")
        return np.array([])

    try:
        # Core features
        base_features = ['latency_ms', 'jitter_ms', 'queue_size']
        available_base = [col for col in base_features if col in df.columns]

        if not available_base:
            logger.error(f"No base features found in DataFrame")
            return np.array([])

        # Start with available base features
        features = df[available_base].values

        # Add system metrics if requested and available
        if include_system_metrics:
            metric_cols = ['cpu_percent', 'memory_percent', 'disk_percent']
            for col in metric_cols:
                if col in df.columns:
                    features = np.column_stack([
                        features,
                        df[col].fillna(0).values
                    ])

        logger.debug(f"Extracted {features.shape[0]} samples, {features.shape[1]} features")
        return features

    except Exception as e:
        logger.error(f"Feature extraction failed: {e}", exc_info=True)
        return np.array([])


def calculate_statistics(
    df: pd.DataFrame,
    window_size: int = 100
) -> Dict[str, Any]:
    """
    Calculate statistics from telemetry.

    Args:
        df: Telemetry DataFrame
        window_size: Rolling window size

    Returns:
        dict: Statistics dictionary
    """
    if df.empty:
        return {}

    try:
        stats = {
            "count": len(df),
            "timestamp_range": None,
            "latency": {},
            "queue_size": {},
            "trends": {}
        }

        if 'timestamp' in df.columns:
            stats["timestamp_range"] = {
                "start": df['timestamp'].min().isoformat(),
                "end": df['timestamp'].max().isoformat()
            }

        # Latency statistics
        if 'latency_ms' in df.columns:
            stats["latency"] = {
                "mean": float(df['latency_ms'].mean()),
                "median": float(df['latency_ms'].median()),
                "min": float(df['latency_ms'].min()),
                "max": float(df['latency_ms'].max()),
                "std": float(df['latency_ms'].std())
            }

            # Latency trend
            if len(df) > 1:
                z = np.polyfit(range(len(df)), df['latency_ms'].values, 1)
                stats["trends"]["latency_slope"] = float(z[0])

        # Queue size statistics
        if 'queue_size' in df.columns:
            stats["queue_size"] = {
                "mean": float(df['queue_size'].mean()),
                "max": int(df['queue_size'].max()),
                "min": int(df['queue_size'].min())
            }

        return stats

    except Exception as e:
        logger.error(f"Statistics calculation failed: {e}")
        return {}