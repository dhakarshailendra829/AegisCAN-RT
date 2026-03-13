"""
Priority-based async task scheduler for real-time operations.

Features:
- Priority queue processing
- Async task support
- Exception handling
- Task timeout support
- Graceful shutdown
"""

import asyncio
import logging
from typing import Callable, Any, Awaitable, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """Information about a scheduled task."""
    priority: int
    coro: Callable[..., Awaitable[Any]]
    args: Tuple
    kwargs: dict
    created_at: datetime
    timeout: Optional[float] = None


class TaskScheduler:
    """
    Async priority-based task scheduler for real-time operations.

    Lower priority numbers execute first.

    Features:
    - Priority queue processing
    - Task timeout support
    - Exception isolation
    - Graceful shutdown
    """

    def __init__(self, max_queue_size: int = 1000):
        """
        Initialize scheduler.

        Args:
            max_queue_size: Maximum queue size
        """
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self.running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._processed_count = 0
        self._error_count = 0
        self._logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Start the scheduler."""
        if self.running:
            self._logger.warning("Scheduler already running")
            return

        self.running = True
        self._worker_task = asyncio.create_task(self._worker())
        self._logger.info("Scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if not self.running:
            return

        self.running = False

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        self._logger.info("Scheduler stopped")

    async def add_task(
        self,
        priority: int,
        coro: Callable[..., Awaitable[Any]],
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> None:
        """
        Add async task to scheduler.

        Args:
            priority: Task priority (lower = higher priority)
            coro: Coroutine function
            args: Positional arguments
            timeout: Task timeout in seconds
            kwargs: Keyword arguments
        """
        task = ScheduledTask(
            priority=priority,
            coro=coro,
            args=args,
            kwargs=kwargs,
            created_at=datetime.now(),
            timeout=timeout
        )

        try:
            await asyncio.wait_for(
                self.queue.put(task),
                timeout=5.0
            )
            self._logger.debug(f"Task added with priority {priority}")
        except asyncio.TimeoutError:
            self._logger.error(f"Failed to add task - queue timeout")
            raise

    async def _worker(self) -> None:
        """Main scheduler worker loop."""
        self._logger.info("Scheduler worker started")

        while self.running:
            try:
                task = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                try:
                    if task.timeout:
                        result = await asyncio.wait_for(
                            task.coro(*task.args, **task.kwargs),
                            timeout=task.timeout
                        )
                    else:
                        result = await task.coro(*task.args, **task.kwargs)

                    self._processed_count += 1
                    self._logger.debug(
                        f"Task completed (prio {task.priority}): {result}"
                    )

                except asyncio.TimeoutError:
                    self._error_count += 1
                    self._logger.error(
                        f"Task timeout (prio {task.priority}): "
                        f"{task.coro.__name__}"
                    )

                except Exception as e:
                    self._error_count += 1
                    self._logger.error(
                        f"Task failed (prio {task.priority}): {e}",
                        exc_info=True
                    )

                finally:
                    self.queue.task_done()

            except asyncio.TimeoutError:
                continue  # No task available, keep waiting

            except asyncio.CancelledError:
                self._logger.info("Scheduler worker cancelled")
                break

            except Exception as e:
                self._logger.error(f"Scheduler worker error: {e}", exc_info=True)

        self._logger.info("Scheduler worker stopped")

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()

    def health_status(self) -> dict:
        """Get scheduler health status."""
        return {
            "running": self.running,
            "queue_size": self.queue.qsize(),
            "processed_tasks": self._processed_count,
            "failed_tasks": self._error_count
        }


# Global scheduler instance
scheduler = TaskScheduler()