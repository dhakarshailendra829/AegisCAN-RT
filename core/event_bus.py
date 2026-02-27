import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List
import logging

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Any]]] = defaultdict(list)

    def subscribe(self, topic: str, callback: Callable[[Any], Any]) -> None:
        self._subscribers[topic].append(callback)
        logger.debug(f"Subscribed to topic '{topic}': {callback.__name__ if hasattr(callback, '__name__') else str(callback)}")

    def unsubscribe(self, topic: str, callback: Callable[[Any], Any]) -> None:
        if topic in self._subscribers:
            self._subscribers[topic] = [cb for cb in self._subscribers[topic] if cb is not callback]
            if not self._subscribers[topic]:
                del self._subscribers[topic]

    async def publish(self, topic: str, data: Any = None) -> None:
        if topic not in self._subscribers:
            return

        callbacks = self._subscribers[topic][:]  

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as exc:
                logger.exception(f"Event handler failed for topic '{topic}': {exc}")

event_bus = EventBus()