"""
Time series latency prediction and trend analysis.

Predicts latency trends and detects degradation.
"""

import logging
from typing import Optional
from collections import deque
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from core.event_bus import event_bus, EventTopic

logger = logging.getLogger(__name__)

@dataclass
class LatencyTrend:
    timestamp: datetime
    slope: float
    trend_direction: str  
    confidence: float
    prediction: Optional[float] = None

class LatencyPredictor:
    def __init__(self, window_size: int = 100):
        self.latencies = deque(maxlen=window_size)
        self._logger = logging.getLogger(__name__)
        self._threshold_slope = 50.0  
        self._min_samples = 20

    async def on_can_tx_event(self, data: dict) -> None:
        try:
            latency = data.get("latency_us")
            if latency is not None:
                self.latencies.append(latency)

                if len(self.latencies) >= self._min_samples:
                    trend = await self.analyze_trend()
                    if trend:
                        await self._check_degradation(trend)

        except Exception as e:
            self._logger.error(f"Error processing CAN TX event: {e}")

    async def analyze_trend(self) -> Optional[LatencyTrend]:
        try:
            if len(self.latencies) < self._min_samples:
                return None

            arr = np.array(list(self.latencies))
            z = np.polyfit(range(len(arr)), arr, 1)
            slope = z[0]

            if slope > 10:
                trend_direction = "degrading"
                confidence = min(abs(slope) / 100, 1.0)
            elif slope < -10:
                trend_direction = "improving"
                confidence = min(abs(slope) / 100, 1.0)
            else:
                trend_direction = "stable"
                confidence = 1.0 - min(abs(slope) / 100, 1.0)

            prediction = float(np.polyval(z, len(arr)))

            trend = LatencyTrend(
                timestamp=datetime.now(),
                slope=slope,
                trend_direction=trend_direction,
                confidence=confidence,
                prediction=prediction
            )

            self._logger.debug(
                f"Latency trend: {trend_direction} (slope={slope:.2f}µs/sample, "
                f"confidence={confidence:.1%})"
            )

            return trend

        except Exception as e:
            self._logger.error(f"Trend analysis failed: {e}")
            return None

    async def _check_degradation(self, trend: LatencyTrend) -> None:
        if trend.slope > self._threshold_slope and trend.confidence > 0.7:
            self._logger.warning(
                f"Latency degradation detected: slope={trend.slope:.2f}µs/sample"
            )

            await event_bus.publish(
                EventTopic.ERROR.value,
                {
                    "type": "LATENCY_DEGRADATION",
                    "severity": "MEDIUM",
                    "slope": trend.slope,
                    "prediction": trend.prediction,
                    "confidence": trend.confidence,
                    "timestamp": trend.timestamp.isoformat()
                }
            )

    def get_statistics(self) -> dict:
        if not self.latencies:
            return {}

        arr = np.array(list(self.latencies))
        return {
            "count": len(self.latencies),
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "p95": float(np.percentile(arr, 95)),
            "p99": float(np.percentile(arr, 99))
        }

    def health_status(self) -> dict:
        return {
            "samples": len(self.latencies),
            "max_window": self.latencies.maxlen,
            "statistics": self.get_statistics()
        }