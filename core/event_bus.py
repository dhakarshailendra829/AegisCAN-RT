# core/event_bus.py
import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """Async publish-subscribe event bus using asyncio.

    Supports both sync and async callbacks.
    Safe for use in FastAPI / asyncio applications.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Any]]] = defaultdict(list)

    def subscribe(self, topic: str, callback: Callable[[Any], Any]) -> None:
        """Subscribe to a topic. Callback can be sync or async."""
        self._subscribers[topic].append(callback)
        logger.debug(f"Subscribed to topic '{topic}': {callback.__name__ if hasattr(callback, '__name__') else str(callback)}")

    def unsubscribe(self, topic: str, callback: Callable[[Any], Any]) -> None:
        """Unsubscribe from a topic."""
        if topic in self._subscribers:
            self._subscribers[topic] = [cb for cb in self._subscribers[topic] if cb is not callback]
            if not self._subscribers[topic]:
                del self._subscribers[topic]

    async def publish(self, topic: str, data: Any = None) -> None:
        """Publish event asynchronously to all subscribers.
        
        Handles both sync and async callbacks without blocking.
        """
        if topic not in self._subscribers:
            return

        callbacks = self._subscribers[topic][:]  # copy to avoid modification issues

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as exc:
                logger.exception(f"Event handler failed for topic '{topic}': {exc}")

# Global singleton instance – import and use everywhere
event_bus = EventBus()