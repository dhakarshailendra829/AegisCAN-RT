# core/scheduler.py
import asyncio
from asyncio import PriorityQueue
from typing import Callable, Any, Awaitable
import logging

logger = logging.getLogger(__name__)

class TaskScheduler:
    """Async priority-based task scheduler for real-time operations"""
    
    def __init__(self):
        self.queue: PriorityQueue = PriorityQueue()
        self.running = False
        self._worker_task: asyncio.Task | None = None

    async def start(self):
        if self.running:
            return
        self.running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("Scheduler started")

    async def stop(self):
        if not self.running:
            return
        self.running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler stopped")

    async def add_task(self, priority: int, coro: Callable[..., Awaitable[Any]], *args, **kwargs):
        """Add async task with priority (lower number = higher priority)"""
        await self.queue.put((priority, coro, args, kwargs))
        logger.debug(f"Task added with priority {priority}")

    async def _worker(self):
        while self.running:
            try:
                priority, coro, args, kwargs = await self.queue.get()
                try:
                    result = await coro(*args, **kwargs)
                    logger.debug(f"Task completed (prio {priority}): {result}")
                except Exception as e:
                    logger.error(f"Task failed (prio {priority}): {e}")
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler worker error: {e}")

# Global instance (can be imported and used across the app)
scheduler = TaskScheduler()