"""
Async task lifecycle management.

Features:
- Named task tracking
- Cancellation handling
- Health monitoring
- Graceful shutdown
- Exception tracking
"""

import asyncio
import logging
from typing import Dict, Any, Awaitable, Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TaskInfo:
    name: str
    task: asyncio.Task
    created_at: datetime
    cancelled: bool = False
    error: Optional[Exception] = None

    def is_running(self) -> bool:
        return not self.task.done()

    def get_exception(self) -> Optional[Exception]:
        if self.task.done():
            try:
                self.task.result()
            except asyncio.CancelledError:
                return None
            except Exception as e:
                return e
        return None

class TaskManager:
    def __init__(self):
        self._tasks: Dict[str, TaskInfo] = {}
        self._logger = logging.getLogger(__name__)

    def start_task(
        self,
        name: str,
        coro: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> asyncio.Task:
        if name in self._tasks:
            task_info = self._tasks[name]
            if task_info.is_running():
                self._logger.warning(f"Task '{name}' already running – skipping start")
                return task_info.task

        task = asyncio.create_task(coro(*args, **kwargs), name=name)
        task_info = TaskInfo(name=name, task=task, created_at=datetime.now())
        self._tasks[name] = task_info

        def _task_done_callback(t: asyncio.Task) -> None:
            task_info.error = task_info.get_exception()
            if task_info.error and not isinstance(task_info.error, asyncio.CancelledError):
                self._logger.error(f"Task '{name}' failed: {task_info.error}")
            self._logger.debug(f"Task '{name}' completed")

        task.add_done_callback(_task_done_callback)

        self._logger.info(f"Started task: {name}")
        return task

    def cancel_task(self, name: str, timeout: float = 5.0) -> bool:
        task_info = self._tasks.get(name)
        if not task_info or task_info.task.done():
            return False

        task_info.cancelled = True
        task_info.task.cancel()
        self._logger.info(f"Cancelled task: {name}")
        return True

    async def cancel_task_async(self, name: str, timeout: float = 5.0) -> bool:
        task_info = self._tasks.get(name)
        if not task_info or task_info.task.done():
            return False

        task_info.cancelled = True
        task_info.task.cancel()

        try:
            await asyncio.wait_for(asyncio.shield(task_info.task), timeout=timeout)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

        self._logger.info(f"Async cancelled task: {name}")
        return True

    def get_task(self, name: str) -> Optional[asyncio.Task]:
        task_info = self._tasks.get(name)
        return task_info.task if task_info else None

    def get_task_info(self, name: str) -> Optional[TaskInfo]:
        return self._tasks.get(name)

    def list_tasks(self) -> List[str]:
        return [name for name, info in self._tasks.items() if info.is_running()]

    def health_status(self) -> Dict[str, Any]:
        running = sum(1 for info in self._tasks.values() if info.is_running())
        failed = sum(1 for info in self._tasks.values() if info.error is not None)

        return {
            "total_tasks": len(self._tasks),
            "running_tasks": running,
            "completed_tasks": len(self._tasks) - running,
            "failed_tasks": failed,
            "tasks": {
                name: {
                    "running": info.is_running(),
                    "created_at": info.created_at.isoformat(),
                    "error": str(info.error) if info.error else None
                }
                for name, info in self._tasks.items()
            }
        }

    async def shutdown_all(self, timeout: float = 30.0) -> Dict[str, bool]:
        self._logger.info(f"Shutting down {len(self._tasks)} tasks")

        results = {}
        tasks_to_cancel = [
            (name, info) for name, info in self._tasks.items() if info.is_running()
        ]

        for name, info in tasks_to_cancel:
            info.task.cancel()

        if tasks_to_cancel:
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        *[info.task for _, info in tasks_to_cancel],
                        return_exceptions=True
                    ),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                self._logger.warning(f"Task shutdown timeout after {timeout}s")

        for name, info in self._tasks.items():
            results[name] = info.task.done()

        self._logger.info("All tasks shutdown complete")
        return results

task_manager = TaskManager()