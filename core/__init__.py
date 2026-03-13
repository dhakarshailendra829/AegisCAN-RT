"""
Core module initialization.

Provides centralized access to core components:
- Event bus for pub/sub messaging
- Logger for structured logging
- Task manager for async task lifecycle
- Metrics engine for performance monitoring
- Scheduler for priority-based task execution
"""

from core.event_bus import event_bus, EventBus
from core.logger_engine import get_logger, LoggerEngine
from core.task_manager import task_manager, TaskManager
from core.metrics_engine import metrics_engine, MetricsEngine
from core.scheduler import scheduler, TaskScheduler

__all__ = [
    "event_bus",
    "EventBus",
    "get_logger",
    "LoggerEngine",
    "task_manager",
    "TaskManager",
    "metrics_engine",
    "MetricsEngine",
    "scheduler",
    "TaskScheduler",
]

__version__ = "0.1.0"