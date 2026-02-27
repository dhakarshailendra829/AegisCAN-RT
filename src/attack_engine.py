import asyncio
import random
from core.logger_engine import logger
from core.event_bus import event_bus


class AttackEngine:
    def __init__(self, event_bus=event_bus):
        self.event_bus = event_bus

    async def dos_attack(self, duration_sec: float = 2.0, rate_hz: float = 100.0):
        logger.warning(f"Starting DoS attack simulation: {duration_sec}s @ {rate_hz} Hz")
        end_time = asyncio.get_running_loop().time() + duration_sec
        interval = 1.0 / rate_hz if rate_hz > 0 else 0.1

        count = 0
        try:
            while asyncio.get_running_loop().time() < end_time:
                await self.event_bus.publish("attack.event", {
                    "type": "DOS",
                    "severity": "HIGH",
                    "timestamp": asyncio.get_running_loop().time(),
                    "simulated_rate_hz": rate_hz,
                    "event_count": count + 1
                })
                count += 1
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("DoS attack cancelled")
        except Exception as e:
            logger.error(f"DoS attack failed: {e}", exc_info=True)
        finally:
            logger.info(f"DoS simulation ended after {count} events")

    async def bit_flip(self):
        try:
            await self.event_bus.publish("attack.event", {
                "type": "BIT_FLIP",
                "severity": "MEDIUM",
                "description": "Random bit flip injected in steering data",
                "timestamp": asyncio.get_running_loop().time()
            })
            logger.warning("Bit-flip attack event published")
        except Exception as e:
            logger.error(f"Bit-flip attack publish failed: {e}", exc_info=True)

    async def heartbeat_drop(self):
        try:
            await self.event_bus.publish("attack.event", {
                "type": "HEARTBEAT_LOSS",
                "severity": "CRITICAL",
                "description": "Heartbeat messages dropped - potential node isolation",
                "timestamp": asyncio.get_running_loop().time()
            })
            logger.warning("Heartbeat drop attack event published")
        except Exception as e:
            logger.error(f"Heartbeat drop attack publish failed: {e}", exc_info=True)