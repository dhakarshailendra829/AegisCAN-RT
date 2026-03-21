"""
Cybersecurity attack simulation engine for testing detection.

Simulates:
- Denial of Service (DoS) attacks
- Bit-flip attacks
- Heartbeat loss attacks

Features:
- Configurable attack parameters
- Event publishing
- Graceful cancellation
- Error tracking
"""

import asyncio
import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum
from core.event_bus import event_bus, EventTopic

logger = logging.getLogger(__name__)

class AttackType(str, Enum):
    """Attack simulation types."""
    DOS = "DOS"
    BIT_FLIP = "BIT_FLIP"
    HEARTBEAT_LOSS = "HEARTBEAT_LOSS"

class SeverityLevel(str, Enum):
    """Attack severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class AttackEvent:
    """Attack simulation event."""
    type: AttackType
    severity: SeverityLevel
    description: str
    timestamp: float
    duration_sec: Optional[float] = None
    rate_hz: Optional[float] = None
    event_count: int = 0

class AttackEngine:
    def __init__(self):
        """Initialize attack engine."""
        self._logger = logging.getLogger(__name__)
        self._current_attack: Optional[asyncio.Task] = None
        self._attack_count = 0

    async def dos_attack(
        self,
        duration_sec: float = 3.0,
        rate_hz: float = 80.0
    ) -> None:
        self._logger.warning(
            f"Starting DoS attack: {duration_sec}s @ {rate_hz} Hz"
        )

        end_time = asyncio.get_running_loop().time() + duration_sec
        interval = 1.0 / rate_hz if rate_hz > 0 else 0.1
        event_count = 0

        try:
            while asyncio.get_running_loop().time() < end_time:
                event_count += 1

                await event_bus.publish(
                    EventTopic.ATTACK_EVENT.value,
                    {
                        "type": AttackType.DOS.value,
                        "severity": SeverityLevel.HIGH.value,
                        "timestamp": asyncio.get_running_loop().time(),
                        "simulated_rate_hz": rate_hz,
                        "event_count": event_count,
                        "description": f"DoS attack - {event_count} messages sent"
                    }
                )

                self._logger.debug(f"DoS attack event #{event_count}")
                await asyncio.sleep(interval)

            self._logger.info(f"DoS attack completed: {event_count} events sent")

        except asyncio.CancelledError:
            self._logger.info(f"DoS attack cancelled after {event_count} events")
            raise

        except Exception as e:
            self._logger.error(f"DoS attack failed: {e}", exc_info=True)
            raise

    async def bit_flip(self) -> None:
        self._logger.warning("Executing bit-flip attack")

        try:
            await event_bus.publish(
                EventTopic.ATTACK_EVENT.value,
                {
                    "type": AttackType.BIT_FLIP.value,
                    "severity": SeverityLevel.MEDIUM.value,
                    "description": "Random bit flip injected in steering data",
                    "timestamp": asyncio.get_running_loop().time(),
                    "event_count": 1
                }
            )

            self._logger.info("Bit-flip attack event published")

        except Exception as e:
            self._logger.error(f"Bit-flip attack failed: {e}", exc_info=True)
            raise

    async def heartbeat_drop(self, duration_sec: float = 5.0) -> None:
        self._logger.warning(f"Starting heartbeat drop attack ({duration_sec}s)")

        end_time = asyncio.get_running_loop().time() + duration_sec
        event_count = 0

        try:
            while asyncio.get_running_loop().time() < end_time:
                event_count += 1

                await event_bus.publish(
                    EventTopic.ATTACK_EVENT.value,
                    {
                        "type": AttackType.HEARTBEAT_LOSS.value,
                        "severity": SeverityLevel.CRITICAL.value,
                        "description": "Heartbeat messages dropped - potential node isolation",
                        "timestamp": asyncio.get_running_loop().time(),
                        "duration_sec": duration_sec,
                        "event_count": event_count
                    }
                )

                self._logger.debug(f"Heartbeat loss event #{event_count}")
                await asyncio.sleep(1.0)

            self._logger.info(f"Heartbeat drop attack completed: {event_count} events")

        except asyncio.CancelledError:
            self._logger.info(f"Heartbeat drop attack cancelled after {event_count} events")
            raise

        except Exception as e:
            self._logger.error(f"Heartbeat drop attack failed: {e}", exc_info=True)
            raise

    def health_status(self) -> dict:
        return {
            "current_attack": None if not self._current_attack or self._current_attack.done() else "active",
            "total_attacks": self._attack_count
        }