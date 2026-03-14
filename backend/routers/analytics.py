"""
Enhanced analytics router with ML model integration.
(This expands on the previous backend/routers/analytics.py)
"""

import logging
import sqlite3
import json
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, HTTPException, status

from backend.config import settings
from backend.schemas.models import TelemetryResponse, TelemetryEntry, ErrorResponse
from analytics.anomaly_detector import AnomalyDetector
from analytics.cyber_attack_classifier import CyberAttackClassifier
from analytics.latency_predictor import LatencyPredictor
from analytics.system_health_ai import SystemHealthMonitor
import pandas as pd

logger = logging.getLogger(__name__)

router = APIRouter()

anomaly_detector = AnomalyDetector(contamination=0.05)
attack_classifier = CyberAttackClassifier()
latency_predictor = LatencyPredictor(window_size=100)
health_monitor = SystemHealthMonitor()


def get_db_path() -> str:
    """Get database file path."""
    return str(settings.DATABASE_URL).replace("sqlite+aiosqlite:///", "")


@router.get("/anomalies/detect")
async def detect_anomalies(
    limit: int = Query(100, ge=1, le=1000),
    threshold: float = Query(0.1, ge=0, le=1)
):
    """
    Detect anomalies in recent telemetry using ML.

    Args:
        limit: Number of recent samples
        threshold: Anomaly alert threshold (0-1)

    Returns:
        dict: Anomaly detection results
    """
    try:
        db_path = get_db_path()

        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(
                f"SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT {limit}",
                conn
            )

        if df.empty:
            return {
                "status": "no_data",
                "message": "Insufficient telemetry data",
                "anomalies": []
            }

        predictions, event = await anomaly_detector.detect(df, threshold=threshold)

        if event is None:
            return {
                "status": "success",
                "anomalies": [],
                "anomaly_ratio": 0
            }

        return {
            "status": "success",
            "anomaly_ratio": event.anomaly_ratio,
            "anomaly_count": event.anomaly_count,
            "total_samples": event.total_samples,
            "severity": event.severity,
            "timestamp": event.timestamp.isoformat(),
            "predictions": predictions.tolist()
        }

    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anomaly detection failed: {str(e)}"
        )


@router.get("/attacks/classify")
async def classify_attack(
    limit: int = Query(50, ge=1, le=500)
):
    """
    Classify attacks in recent telemetry.

    Returns:
        dict: Attack classification results
    """
    try:
        db_path = get_db_path()

        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(
                f"SELECT * FROM telemetry WHERE type='ATTACK' "
                f"ORDER BY timestamp DESC LIMIT {limit}",
                conn
            )

        if df.empty:
            return {
                "status": "no_attacks",
                "message": "No recent attacks detected",
                "classifications": []
            }

        from analytics.utils import extract_features, preprocess_telemetry

        processed = preprocess_telemetry(df)
        X = extract_features(processed)

        predictions = []
        for features in X:
            pred = await attack_classifier.classify(features)
            if pred:
                predictions.append({
                    "type": pred.attack_type,
                    "confidence": pred.confidence,
                    "timestamp": pred.timestamp.isoformat(),
                    "probabilities": pred.probabilities
                })

        return {
            "status": "success",
            "attack_count": len(df),
            "classifications": predictions
        }

    except Exception as e:
        logger.error(f"Attack classification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )

@router.get("/latency/trends")
async def get_latency_trends():
    """
    Get latency trend analysis.

    Returns:
        dict: Latency statistics and trends
    """
    return {
        "status": "success",
        "statistics": latency_predictor.get_statistics(),
        "health": latency_predictor.health_status()
    }


@router.get("/health/status")
async def get_health_status():
    """
    Get system health status.

    Returns:
        dict: Health metrics and alerts
    """
    return {
        "status": "success",
        "health_monitor": health_monitor.health_status(),
        "anomaly_detector": anomaly_detector.health_status(),
        "attack_classifier": attack_classifier.health_status(),
        "latency_predictor": latency_predictor.health_status()
    }

@router.post("/health/thresholds")
async def update_health_thresholds(
    cpu: Optional[float] = None,
    memory: Optional[float] = None,
    disk: Optional[float] = None
):
    """
    Update system health alert thresholds.

    Args:
        cpu: CPU threshold percentage
        memory: Memory threshold percentage
        disk: Disk threshold percentage

    Returns:
        dict: Updated thresholds
    """
    try:
        health_monitor.update_thresholds(cpu=cpu, memory=memory, disk=disk)

        return {
            "status": "success",
            "message": "Thresholds updated",
            "thresholds": health_monitor.health_status()["thresholds"]
        }

    except Exception as e:
        logger.error(f"Failed to update thresholds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update thresholds: {str(e)}"
        )