# analytics/anomaly_detector.py
from sklearn.ensemble import IsolationForest
import joblib
import numpy as np
from pathlib import Path
from typing import Tuple
import pandas as pd
import numpy as np
from core.logger_engine import logger
from core.event_bus import event_bus
from analytics.utils import extract_features, preprocess_telemetry

MODEL_PATH = Path("analytics/models/anomaly_model.pkl")

class AnomalyDetector:
    def __init__(self, contamination: float = 0.05):
        self.model = None
        self.contamination = contamination
        self._load_or_train()

    def _load_or_train(self):
        if MODEL_PATH.exists():
            self.model = joblib.load(MODEL_PATH)
            logger.info(f"Loaded anomaly model from {MODEL_PATH}")
        else:
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100
            )
            logger.warning("No pre-trained anomaly model found — will train on first data")

    def train(self, df: pd.DataFrame):
        """Train on telemetry DataFrame."""
        if df.empty:
            logger.warning("No data to train anomaly detector")
            return
        X = extract_features(preprocess_telemetry(df))
        if len(X) < 10:
            logger.warning("Too few samples to train")
            return

        self.model.fit(X)
        joblib.dump(self.model, MODEL_PATH)
        logger.info(f"Anomaly model trained and saved to {MODEL_PATH}")

    async def detect(self, df: pd.DataFrame) -> Tuple[np.ndarray, float]:
        """Detect anomalies in recent telemetry."""
        if df.empty or self.model is None:
            return np.array([]), 0.0

        X = extract_features(preprocess_telemetry(df.tail(100)))  # last 100 points
        if len(X) == 0:
            return np.array([]), 0.0

        predictions = self.model.predict(X)  # -1 = anomaly, 1 = normal
        anomaly_scores = self.model.decision_function(X)
        anomaly_ratio = (predictions == -1).mean()

        if anomaly_ratio > 0.1:
            await event_bus.publish("anomaly.detected", {
                "ratio": anomaly_ratio,
                "scores": anomaly_scores.tolist(),
                "timestamp": df['timestamp'].iloc[-1] if 'timestamp' in df else None
            })

        return predictions, anomaly_ratio