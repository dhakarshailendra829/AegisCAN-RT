import psutil
import time
import threading

class MetricsEngine:
    def __init__(self,event_bus):

        self.bus = event_bus
        self.running = True

    def collect(self):

        while self.running:

            stats = {
                "cpu": psutil.cpu_percent(),
                "ram": psutil.virtual_memory().percent,
                "threads": threading.active_count(),
                "time": time.time()
            }

            self.bus.publish("system.metrics", stats)

            time.sleep(1)

    def start(self):
        threading.Thread(target=self.collect, daemon=True).start()

    def stop(self):
        self.running=False
# core/metrics_engine.py
import asyncio
import psutil
import time
from typing import Any

from core.event_bus import event_bus
from core.logger_engine import logger

class MetricsEngine:
    """Async background metrics collector using asyncio.
    
    Publishes system metrics to event_bus every few seconds.
    """

    def __init__(self, interval: float = 5.0):  # configurable interval
        self.interval = interval
        self._task: asyncio.Task | None = None
        self.running = False

    async def collect(self):
        """Infinite async loop collecting metrics."""
        while self.running:
            try:
                stats = {
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "ram_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent,
                    "active_threads": len(asyncio.all_tasks()),  # better than threading
                    "timestamp": time.time(),
                }
                await event_bus.publish("system.metrics", stats)
                logger.debug("Published system metrics", extra=stats)
            except Exception as exc:
                logger.error("Metrics collection failed", exc_info=True)

            await asyncio.sleep(self.interval)

    def start(self):
        """Start background collection task."""
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_task(self.collect())
        logger.info("MetricsEngine started")

    async def stop(self):
        """Gracefully stop the collector."""
        if not self.running:
            return
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MetricsEngine stopped")

# Global instance
metrics_engine = MetricsEngine(interval=5.0)