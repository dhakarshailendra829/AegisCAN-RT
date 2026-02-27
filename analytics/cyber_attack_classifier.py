# analytics/cyber_attack_classifier.py
from sklearn.ensemble import RandomForestClassifier
import joblib
from pathlib import Path
import pandas as pd
import numpy as np
from core.logger_engine import logger
from core.event_bus import event_bus
from analytics.utils import extract_features

MODEL_PATH = Path("analytics/models/classifier_model.joblib")

class CyberAttackClassifier:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        if MODEL_PATH.exists():
            self.model = joblib.load(MODEL_PATH)
            logger.info("Loaded attack classifier model")
        else:
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            logger.warning("No pre-trained classifier — needs training")

    def train(self, X, y):
        if len(X) < 10:
            return
        self.model.fit(X, y)
        joblib.dump(self.model, MODEL_PATH)
        logger.info("Classifier trained and saved")

    async def classify(self, features: np.ndarray) -> str:
        if self.model is None or len(features) == 0:
            return "unknown"
        pred = self.model.predict(features.reshape(1, -1))[0]
        prob = self.model.predict_proba(features.reshape(1, -1)).max()
        label = {0: "normal", 1: "dos", 2: "bit_flip", 3: "replay"}.get(pred, "unknown")

        if prob > 0.7 and label != "normal":
            await event_bus.publish("attack.classified", {
                "type": label,
                "confidence": float(prob)
            })

        return label