"""
Analytics module for AI-powered system monitoring and attack detection.

Provides:
- Anomaly detection
- Cyber attack classification
- Latency prediction
- System health monitoring
"""

from analytics.anomaly_detector import AnomalyDetector, AnomalyEvent
from analytics.cyber_attack_classifier import CyberAttackClassifier, AttackPrediction
from analytics.latency_predictor import LatencyPredictor, LatencyTrend
from analytics.system_health_ai import SystemHealthMonitor, HealthAlert
from analytics.utils import preprocess_telemetry, extract_features, FeatureVector

__all__ = [
    "AnomalyDetector",
    "AnomalyEvent",
    "CyberAttackClassifier",
    "AttackPrediction",
    "LatencyPredictor",
    "LatencyTrend",
    "SystemHealthMonitor",
    "HealthAlert",
    "preprocess_telemetry",
    "extract_features",
    "FeatureVector",
]

__version__ = "0.1.0"