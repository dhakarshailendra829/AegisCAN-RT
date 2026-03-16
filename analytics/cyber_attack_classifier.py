"""
ML-based cyber attack classification.

Classifies detected attacks by type and confidence.
"""

import logging
from typing import Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import RandomForestClassifier
    import joblib
except ImportError:
    RandomForestClassifier = None
    joblib = None

from core.event_bus import event_bus, EventTopic
from analytics.utils import extract_features

logger = logging.getLogger(__name__)

MODEL_PATH = Path("analytics/models/classifier_model.joblib")

ATTACK_TYPES = {
    0: "NORMAL",
    1: "DOS",
    2: "BIT_FLIP",
    3: "HEARTBEAT_LOSS",
    4: "REPLAY",
    5: "UNKNOWN"
}


@dataclass
class AttackPrediction:
    timestamp: datetime
    attack_type: str
    confidence: float
    probabilities: dict


class CyberAttackClassifier:
    def __init__(self):
        self.model = None
        self._logger = logging.getLogger(__name__)
        self._trained = False

        if RandomForestClassifier is None:
            self._logger.warning("scikit-learn not installed - classification disabled")
            return

        self._load_model()

    def _load_model(self) -> None:
        try:
            if MODEL_PATH.exists():
                self.model = joblib.load(MODEL_PATH)
                self._trained = True
                self._logger.info(f"Loaded classifier from {MODEL_PATH}")
            else:
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
                self._logger.info("Created new Random Forest classifier")

        except Exception as e:
            self._logger.error(f"Failed to load classifier: {e}")
            self.model = None

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        if self.model is None or not RandomForestClassifier:
            self._logger.warning("Model unavailable")
            return False

        try:
            if len(X) < 10:
                self._logger.warning(f"Insufficient training samples: {len(X)}")
                return False

            self.model.fit(X, y)
            self._trained = True

            MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.model, MODEL_PATH)

            self._logger.info(
                f"Classifier trained on {len(X)} samples and saved to {MODEL_PATH}"
            )
            return True

        except Exception as e:
            self._logger.error(f"Training failed: {e}", exc_info=True)
            return False

    async def classify(self, features: np.ndarray) -> Optional[AttackPrediction]:
        if self.model is None or not RandomForestClassifier:
            return None

        try:
            if len(features) == 0:
                return None

            if features.ndim == 1:
                features = features.reshape(1, -1)

            pred = self.model.predict(features)[0]
            probs = self.model.predict_proba(features)[0]
            confidence = probs.max()

            attack_type = ATTACK_TYPES.get(pred, "UNKNOWN")

            prediction = AttackPrediction(
                timestamp=datetime.now(),
                attack_type=attack_type,
                confidence=float(confidence),
                probabilities={
                    ATTACK_TYPES.get(i, "UNKNOWN"): float(p)
                    for i, p in enumerate(probs)
                }
            )

            if confidence > 0.7 and attack_type != "NORMAL":
                await event_bus.publish(
                    EventTopic.ATTACK_EVENT.value,
                    {
                        "type": f"ATTACK_CLASSIFIED_{attack_type}",
                        "severity": "HIGH" if confidence > 0.85 else "MEDIUM",
                        "confidence": confidence,
                        "probabilities": prediction.probabilities,
                        "timestamp": prediction.timestamp.isoformat()
                    }
                )

            self._logger.debug(
                f"Classification: {attack_type} ({confidence:.2%})"
            )
            return prediction

        except Exception as e:
            self._logger.error(f"Classification failed: {e}", exc_info=True)
            return None

    def health_status(self) -> dict:
        return {
            "available": self.model is not None,
            "trained": self._trained,
            "attack_types": list(ATTACK_TYPES.values()),
            "model_path": str(MODEL_PATH)
        }