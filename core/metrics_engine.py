"""
System metrics collection and publishing.

Collects:
- CPU usage
- Memory usage
- Disk usage
- Active tasks count
- Custom application metrics
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None

from core.event_bus import event_bus, EventTopic

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System metrics snapshot."""
    timestamp: float
    cpu_percent: Optional[float]
    memory_percent: Optional[float]
    disk_percent: Optional[float]
    active_tasks: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "active_tasks": self.active_tasks
        }


class MetricsEngine:
    """
    Collects and publishes system metrics.

    Features:
    - Configurable collection interval
    - System resource monitoring
    - Event publishing
    - Graceful error handling
    """

    def __init__(self, interval: float = 5.0):
        """
        Initialize metrics engine.

        Args:
            interval: Collection interval in seconds
        """
        self.interval = interval
        self._task: Optional[asyncio.Task] = None
        self.running = False
        self._last_metrics: Optional[SystemMetrics] = None
        self._logger = logging.getLogger(__name__)

        if psutil is None:
            self._logger.warning(
                "psutil not installed - system metrics collection disabled"
            )

    async def collect(self) -> None:
        """Collect metrics in loop."""
        self._logger.info(f"Metrics collection started (interval={self.interval}s)")

        while self.running:
            try:
                metrics = self._gather_metrics()
                self._last_metrics = metrics

                # Publish metrics event
                await event_bus.publish(
                    EventTopic.SYSTEM_METRICS.value,
                    metrics.to_dict()
                )

                self._logger.debug(
                    f"Metrics: CPU={metrics.cpu_percent}%, "
                    f"MEM={metrics.memory_percent}%, "
                    f"DISK={metrics.disk_percent}%, "
                    f"TASKS={metrics.active_tasks}"
                )

            except Exception as exc:
                self._logger.error(
                    f"Metrics collection failed: {exc}",
                    exc_info=True
                )

            await asyncio.sleep(self.interval)

    def _gather_metrics(self) -> SystemMetrics:
        """Gather system metrics."""
        if psutil is None:
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=None,
                memory_percent=None,
                disk_percent=None,
                active_tasks=len(asyncio.all_tasks())
            )

        try:
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=psutil.cpu_percent(interval=0.1),
                memory_percent=psutil.virtual_memory().percent,
                disk_percent=psutil.disk_usage('/').percent,
                active_tasks=len(asyncio.all_tasks())
            )
        except Exception as e:
            self._logger.error(f"Failed to gather metrics: {e}")
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=None,
                memory_percent=None,
                disk_percent=None,
                active_tasks=len(asyncio.all_tasks())
            )

    def start(self) -> None:
        """Start metrics collection."""
        if self.running:
            self._logger.warning("Metrics engine already running")
            return

        self.running = True
        self._task = asyncio.create_task(self.collect())
        self._logger.info("MetricsEngine started")

    async def stop(self) -> None:
        """Stop metrics collection gracefully."""
        if not self.running:
            return

        self.running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._logger.info("MetricsEngine stopped")

    def get_last_metrics(self) -> Optional[SystemMetrics]:
        """Get last collected metrics."""
        return self._last_metrics

    def health_status(self) -> Dict[str, Any]:
        """Get metrics engine health status."""
        return {
            "running": self.running,
            "interval": self.interval,
            "last_metrics": self._last_metrics.to_dict() if self._last_metrics else None,
            "psutil_available": psutil is not None
        }


# Global metrics engine instance
metrics_engine = MetricsEngine(interval=5.0)