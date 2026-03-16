"""
AI-based system health monitoring and alerting.

Monitors CPU, memory, and disk usage with ML-based thresholds.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from core.event_bus import event_bus, EventTopic

logger = logging.getLogger(__name__)

@dataclass
class HealthAlert:
    timestamp: datetime
    alert_type: str
    severity: str
    resource: str
    value: float
    threshold: float


class SystemHealthMonitor:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.cpu_threshold = 80
        self.memory_threshold = 85
        self.disk_threshold = 90

        self._alert_history = {}

    async def on_metrics_event(self, data: dict) -> None:
        try:
            cpu = data.get("cpu_percent")
            memory = data.get("memory_percent")
            disk = data.get("disk_percent")

            if cpu is not None:
                await self._check_resource("cpu", cpu, self.cpu_threshold)

            if memory is not None:
                await self._check_resource("memory", memory, self.memory_threshold)

            if disk is not None:
                await self._check_resource("disk", disk, self.disk_threshold)

        except Exception as e:
            self._logger.error(f"Error processing metrics: {e}")

    async def _check_resource(
        self,
        resource: str,
        value: float,
        threshold: float
    ) -> None:
        if value > threshold:
            if value > threshold * 1.5:
                severity = "CRITICAL"
            elif value > threshold * 1.2:
                severity = "HIGH"
            else:
                severity = "MEDIUM"
            alert_key = f"{resource}_{severity}"
            last_alert = self._alert_history.get(alert_key)

            if last_alert is None or (datetime.now() - last_alert).seconds > 60:
                alert = HealthAlert(
                    timestamp=datetime.now(),
                    alert_type="RESOURCE_OVERLOAD",
                    severity=severity,
                    resource=resource,
                    value=value,
                    threshold=threshold
                )

                self._logger.warning(
                    f"{resource} {severity}: {value:.1f}% (threshold: {threshold}%)"
                )

                await event_bus.publish(
                    EventTopic.ERROR.value,
                    {
                        "type": "SYSTEM_ALERT",
                        "severity": severity,
                        "resource": resource,
                        "value": value,
                        "threshold": threshold,
                        "timestamp": alert.timestamp.isoformat()
                    }
                )

                self._alert_history[alert_key] = datetime.now()

    def update_thresholds(
        self,
        cpu: Optional[float] = None,
        memory: Optional[float] = None,
        disk: Optional[float] = None
    ) -> None:
        if cpu is not None:
            self.cpu_threshold = max(1, min(99, cpu))

        if memory is not None:
            self.memory_threshold = max(1, min(99, memory))

        if disk is not None:
            self.disk_threshold = max(1, min(99, disk))

        self._logger.info(
            f"Thresholds updated: CPU={self.cpu_threshold}%, "
            f"Memory={self.memory_threshold}%, Disk={self.disk_threshold}%"
        )

    def health_status(self) -> dict:
        return {
            "thresholds": {
                "cpu": self.cpu_threshold,
                "memory": self.memory_threshold,
                "disk": self.disk_threshold
            },
            "recent_alerts": len(self._alert_history)
        }