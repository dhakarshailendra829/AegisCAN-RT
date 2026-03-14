"""
Pub/Sub event bus for decoupled component communication.

Features:
- Topic-based publish/subscribe
- Async callback support
- Exception isolation
- Subscriber tracking
- Type-safe events
"""

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)

class EventTopic(str, Enum):
    """Standard event topics."""
    CAN_TX = "can.tx"
    CAN_RX = "can.rx"
    BLE_TX = "ble.tx"
    BLE_RX = "ble.rx"
    ATTACK_EVENT = "attack.event"
    SYSTEM_METRICS = "system.metrics"
    GATEWAY_START = "gateway.start"
    GATEWAY_STOP = "gateway.stop"
    ERROR = "error"


class EventBus:
    """
    Thread-safe event bus for asynchronous pub/sub messaging.

    Supports:
    - Both async and sync callbacks
    - Exception handling per callback
    - Callback removal
    - Topic enumeration
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Any]]] = defaultdict(list)
        self._active_topics: Set[str] = set()
        self._error_count: int = 0
        self._logger = logging.getLogger(__name__)

    def subscribe(
        self,
        topic: str,
        callback: Callable[[Any], Any],
        once: bool = False
    ) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: Event topic name
            callback: Async or sync callback function
            once: If True, callback fires only once then is removed
        """
        if not callable(callback):
            raise TypeError(f"Callback must be callable, got {type(callback)}")

        if once:
            original_callback = callback

            async def one_time_callback(data: Any) -> None:
                try:
                    if asyncio.iscoroutinefunction(original_callback):
                        await original_callback(data)
                    else:
                        original_callback(data)
                finally:
                    self.unsubscribe(topic, one_time_callback)

            callback = one_time_callback

        self._subscribers[topic].append(callback)
        self._logger.debug(
            f"Subscriber added to '{topic}' "
            f"(total: {len(self._subscribers[topic])})"
        )

    def unsubscribe(self, topic: str, callback: Callable[[Any], Any]) -> bool:
        """
        Unsubscribe a callback from a topic.

        Args:
            topic: Event topic name
            callback: Callback to remove

        Returns:
            bool: True if callback was removed
        """
        if topic not in self._subscribers:
            return False

        original_len = len(self._subscribers[topic])
        self._subscribers[topic] = [
            cb for cb in self._subscribers[topic] if cb is not callback
        ]

        if len(self._subscribers[topic]) < original_len:
            self._logger.debug(f"Subscriber removed from '{topic}'")
            if not self._subscribers[topic]:
                del self._subscribers[topic]
            return True

        return False

    async def publish(
        self,
        topic: str,
        data: Any = None,
        timeout: Optional[float] = None
    ) -> int:
        """
        Publish an event to all subscribers.

        Args:
            topic: Event topic name
            data: Event data payload
            timeout: Timeout for all callbacks (seconds)

        Returns:
            int: Number of successfully executed callbacks
        """
        if topic not in self._subscribers:
            self._logger.debug(f"No subscribers for topic '{topic}'")
            return 0

        self._active_topics.add(topic)
        callbacks = self._subscribers[topic][:]  
        executed = 0

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    if timeout:
                        await asyncio.wait_for(callback(data), timeout=timeout)
                    else:
                        await callback(data)
                else:
                    callback(data)
                executed += 1
            except asyncio.TimeoutError:
                self._error_count += 1
                self._logger.error(
                    f"Callback timeout for topic '{topic}': "
                    f"{callback.__name__ if hasattr(callback, '__name__') else 'unknown'}"
                )
            except Exception as exc:
                self._error_count += 1
                self._logger.error(
                    f"Callback failed for topic '{topic}': {exc}",
                    exc_info=True
                )

        return executed

    def get_subscriber_count(self, topic: str) -> int:
        """Get number of subscribers for a topic."""
        return len(self._subscribers.get(topic, []))

    def get_topics(self) -> List[str]:
        """Get all active topics."""
        return list(self._subscribers.keys())

    def health_status(self) -> Dict[str, Any]:
        """Get event bus health information."""
        return {
            "topics": len(self._subscribers),
            "total_subscribers": sum(len(v) for v in self._subscribers.values()),
            "error_count": self._error_count,
            "active_topics": list(self._active_topics)
        }

event_bus = EventBus()