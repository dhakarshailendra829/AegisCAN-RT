"""
Train ML models for anomaly detection and attack classification.

Usage:
    python scripts/train_models.py --limit 10000 --contamination 0.05
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
import numpy as np
import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent))

from analytics.anomaly_detector import AnomalyDetector
from analytics.cyber_attack_classifier import CyberAttackClassifier
from analytics.utils import extract_features, preprocess_telemetry
from backend.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_telemetry_data(limit: int = 10000) -> pd.DataFrame:
    """
    Load telemetry data from database.

    Args:
        limit: Maximum number of samples

    Returns:
        pd.DataFrame: Telemetry data
    """
    logger.info(f"Loading telemetry data (limit={limit})")

    db_path = str(settings.DATABASE_URL).replace("sqlite+aiosqlite:///", "")

    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(
                f"SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT {limit}",
                conn
            )

        logger.info(f"Loaded {len(df)} telemetry records")
        return df

    except Exception as e:
        logger.error(f"Failed to load telemetry: {e}")
        return pd.DataFrame()


def train_anomaly_detector(df: pd.DataFrame, contamination: float = 0.05) -> bool:
    """
    Train anomaly detection model.

    Args:
        df: Training data
        contamination: Expected anomaly ratio

    Returns:
        bool: Training success
    """
    logger.info("Training anomaly detection model...")

    try:
        detector = AnomalyDetector(contamination=contamination)
        success = detector.train(df)

        if success:
            logger.info("Anomaly detector trained successfully")
            status = detector.health_status()
            logger.info(f"Model path: {status['model_path']}")
        else:
            logger.warning("Anomaly detector training failed")

        return success

    except Exception as e:
        logger.error(f"Anomaly detector training error: {e}", exc_info=True)
        return False


def train_attack_classifier(df: pd.DataFrame) -> bool:
    """
    Train attack classification model.

    Note: Requires labeled data with 'attack_type' column.

    Args:
        df: Training data with labels

    Returns:
        bool: Training success
    """
    logger.info("Training attack classifier...")

    try:
        if "attack_type" not in df.columns:
            logger.warning("No attack labels in data - skipping classifier training")
            return False

        processed = preprocess_telemetry(df)
        X = extract_features(processed)

        label_map = {
            "NORMAL": 0,
            "DOS": 1,
            "BIT_FLIP": 2,
            "HEARTBEAT_LOSS": 3,
            "REPLAY": 4
        }

        y = df["attack_type"].map(label_map).fillna(5).astype(int)

        if len(X) < 10:
            logger.warning(f"Insufficient labeled samples: {len(X)}")
            return False

        classifier = CyberAttackClassifier()
        success = classifier.train(X, y)

        if success:
            logger.info("Attack classifier trained successfully")
            status = classifier.health_status()
            logger.info(f"Model path: {status['model_path']}")
        else:
            logger.warning("Classifier training failed")

        return success

    except Exception as e:
        logger.error(f"Classifier training error: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Train ML models for AegisCAN-RT"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10000,
        help="Maximum telemetry samples"
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.05,
        help="Expected anomaly ratio"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("AegisCAN-RT Model Training")
    logger.info("=" * 60)

    df = load_telemetry_data(limit=args.limit)

    if df.empty:
        logger.error("No training data available")
        return 1

    detector_success = train_anomaly_detector(df, contamination=args.contamination)
    classifier_success = train_attack_classifier(df)
    logger.info("=" * 60)
    logger.info("Training Summary:")
    logger.info(f"  Anomaly Detector: {'✅' if detector_success else '❌'}")
    logger.info(f"  Attack Classifier: {'✅' if classifier_success else '❌'}")
    logger.info("=" * 60)

    return 0 if (detector_success or classifier_success) else 1


if __name__ == "__main__":
    sys.exit(main())