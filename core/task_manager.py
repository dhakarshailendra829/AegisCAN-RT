# core/task_manager.py   ← suggested rename (or keep name and migrate)
import asyncio
from typing import Dict, Any, Awaitable, Callable
import logging

from core.logger_engine import logger

class TaskManager:
    """Manages background asyncio tasks (replacement for old ThreadManager)."""

    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}

    def start_task(self, name: str, coro: Callable[..., Awaitable[Any]], *args, **kwargs) -> asyncio.Task:
        """Start an async task and track it by name."""
        if name in self._tasks and not self._tasks[name].done():
            logger.warning(f"Task '{name}' already running – not starting duplicate")
            return self._tasks[name]

        task = asyncio.create_task(coro(*args, **kwargs), name=name)
        self._tasks[name] = task
        logger.info(f"Started task: {name}")

        # Auto-remove when done
        task.add_done_callback(lambda t: self._tasks.pop(name, None))

        return task

    def cancel_task(self, name: str) -> bool:
        """Cancel a running task by name."""
        task = self._tasks.get(name)
        if task and not task.done():
            task.cancel()
            logger.info(f"Cancelled task: {name}")
            return True
        return False

    def health_status(self) -> Dict[str, bool]:
        """Return dict of task names → is_alive (not cancelled/done)."""
        return {name: not task.done() for name, task in self._tasks.items()}

    async def shutdown_all(self):
        """Cancel and await all running tasks."""
        for name, task in list(self._tasks.items()):
            if not task.done():
                task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        logger.info("All tasks cancelled/shutdown")

# Global instance
task_manager = TaskManager()