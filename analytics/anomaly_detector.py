"""
ML-based anomaly detection for telemetry data.

Uses Isolation Forest for unsupervised anomaly detection.
"""

import logging
from typing import Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import IsolationForest
    import joblib
except ImportError:
    IsolationForest = None
    joblib = None

from core.event_bus import event_bus, EventTopic
from analytics.utils import preprocess_telemetry, extract_features

logger = logging.getLogger(__name__)

MODEL_PATH = Path("analytics/models/anomaly_model.joblib")


@dataclass
class AnomalyEvent:
    """Anomaly detection event."""
    timestamp: datetime
    anomaly_ratio: float
    anomaly_count: int
    total_samples: int
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    scores: list


class AnomalyDetector:
    """
    ML-based anomaly detection using Isolation Forest.

    Detects statistical anomalies in telemetry data.
    """

    def __init__(self, contamination: float = 0.05):
        """
        Initialize anomaly detector.

        Args:
            contamination: Expected anomaly ratio (0-1)
        """
        self.model = None
        self.contamination = contamination
        self._logger = logging.getLogger(__name__)
        self._trained = False

        if IsolationForest is None:
            self._logger.warning("scikit-learn not installed - anomaly detection disabled")
            return

        self._load_or_train()

    def _load_or_train(self) -> None:
        """Load existing model or create new one."""
        if not IsolationForest:
            return

        try:
            if MODEL_PATH.exists():
                self.model = joblib.load(MODEL_PATH)
                self._trained = True
                self._logger.info(f"Loaded anomaly model from {MODEL_PATH}")
            else:
                self.model = IsolationForest(
                    contamination=self.contamination,
                    random_state=42,
                    n_estimators=100,
                    max_samples='auto'
                )
                self._logger.info("Created new Isolation Forest model")

        except Exception as e:
            self._logger.error(f"Failed to load/create model: {e}")
            self.model = None

    def train(self, df: pd.DataFrame) -> bool:
        """
        Train detector on telemetry data.

        Args:
            df: Training DataFrame

        Returns:
            bool: Training success
        """
        if self.model is None or not IsolationForest:
            self._logger.warning("Model unavailable")
            return False

        try:
            if df.empty:
                self._logger.warning("Cannot train on empty DataFrame")
                return False

            # Preprocess and extract features
            processed = preprocess_telemetry(df)
            X = extract_features(processed)

            if len(X) < 10:
                self._logger.warning(f"Insufficient training samples: {len(X)}")
                return False

            # Train model
            self.model.fit(X)
            self._trained = True

            # Save model
            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.model, MODEL_PATH)

            self._logger.info(
                f"Model trained on {len(X)} samples and saved to {MODEL_PATH}"
            )
            return True

        except Exception as e:
            self._logger.error(f"Training failed: {e}", exc_info=True)
            return False

    async def detect(
        self,
        df: pd.DataFrame,
        threshold: float = 0.1
    ) -> Tuple[np.ndarray, AnomalyEvent]:
        """
        Detect anomalies in telemetry.

        Args:
            df: Telemetry DataFrame
            threshold: Anomaly ratio threshold for alert

        Returns:
            tuple: (predictions, AnomalyEvent)
        """
        if self.model is None or not IsolationForest:
            return np.array([]), None

        try:
            if df.empty:
                return np.array([]), None

            # Preprocess and extract features
            processed = preprocess_telemetry(df)
            X = extract_features(processed)

            if len(X) == 0:
                return np.array([]), None

            # Predict anomalies
            predictions = self.model.predict(X)  # -1 = anomaly, 1 = normal
            scores = self.model.score_samples(X)

            # Calculate metrics
            anomaly_count = (predictions == -1).sum()
            anomaly_ratio = anomaly_count / len(predictions)

            # Determine severity
            if anomaly_ratio > 0.5:
                severity = "CRITICAL"
            elif anomaly_ratio > 0.3:
                severity = "HIGH"
            elif anomaly_ratio > 0.1:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            # Create event
            event = AnomalyEvent(
                timestamp=datetime.now(),
                anomaly_ratio=anomaly_ratio,
                anomaly_count=int(anomaly_count),
                total_samples=len(predictions),
                severity=severity,
                scores=scores.tolist()
            )

            # Publish if above threshold
            if anomaly_ratio > threshold:
                await event_bus.publish(
                    EventTopic.ATTACK_EVENT.value,
                    {
                        "type": "ANOMALY_DETECTED",
                        "severity": severity,
                        "anomaly_ratio": anomaly_ratio,
                        "count": anomaly_count,
                        "timestamp": datetime.now().isoformat()
                    }
                )

            self._logger.debug(
                f"Anomaly detection: {anomaly_count}/{len(predictions)} "
                f"({anomaly_ratio:.1%}) severity={severity}"
            )

            return predictions, event

        except Exception as e:
            self._logger.error(f"Detection failed: {e}", exc_info=True)
            return np.array([]), None

    def health_status(self) -> dict:
        """Get detector health status."""
        return {
            "available": self.model is not None,
            "trained": self._trained,
            "contamination": self.contamination,
            "model_path": str(MODEL_PATH)
        }