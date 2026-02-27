import asyncio
import psutil
import time
from typing import Any
from core.event_bus import event_bus
from core.logger_engine import logger

class MetricsEngine:
    def __init__(self, interval: float = 5.0):  
        self.interval = interval
        self._task: asyncio.Task | None = None
        self.running = False

    async def collect(self):
        while self.running:
            try:
                stats = {
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "ram_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent,
                    "active_threads": len(asyncio.all_tasks()),  
                    "timestamp": time.time(),
                }
                await event_bus.publish("system.metrics", stats)
                logger.debug("Published system metrics", extra=stats)
            except Exception as exc:
                logger.error("Metrics collection failed", exc_info=True)

            await asyncio.sleep(self.interval)

    def start(self):
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_task(self.collect())
        logger.info("MetricsEngine started")

    async def stop(self):
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

metrics_engine = MetricsEngine(interval=5.0)