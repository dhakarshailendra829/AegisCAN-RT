import asyncio
import socket
import struct
import random
from queue import PriorityQueue, Full, Empty

from core.logger_engine import logger
from core.event_bus import event_bus
from core.task_manager import task_manager

UDP_IP = "127.0.0.1"
UDP_PORT = 5005


class BLEReceiver:
    def __init__(self, event_bus=event_bus, max_queue_size: int = 500):
        self.event_bus = event_bus
        self.queue = PriorityQueue(maxsize=max_queue_size)
        self.running = False
        self._udp_task: asyncio.Task | None = None
        self._simulate_task: asyncio.Task | None = None
        self._sock: socket.socket | None = None

    def create_packet(self, data: bytes, priority: int = 1) -> tuple[int, int, bytes]:
        ts_us = int(asyncio.get_running_loop().time() * 1_000_000)
        return priority, ts_us, data

    async def _udp_forward_loop(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            while self.running:
                try:
                    priority, ts, data = await asyncio.wait_for(
                        asyncio.to_thread(self.queue.get_nowait),
                        timeout=0.1
                    )
                    packet = bytes([priority]) + struct.pack('<Q', ts) + data
                    self._sock.sendto(packet, (UDP_IP, UDP_PORT))

                    await self.event_bus.publish("ble.tx", {
                        "priority": priority,
                        "timestamp_us": ts,
                        "data_len": len(data)
                    })
                except (asyncio.TimeoutError, Empty):
                    continue  
                except Full:
                    logger.warning("Queue full - cannot forward")
                    await asyncio.sleep(0.01)
                except Exception as e:
                    logger.error(f"UDP forward error: {e}", exc_info=True)
                    await asyncio.sleep(0.5)  
        finally:
            if self._sock:
                self._sock.close()
                self._sock = None
            logger.info("UDP forward loop ended")

    async def simulate(self):
        steering_center = 127
        while self.running:
            try:
                steering_val = steering_center + int(55 * random.uniform(-1, 1))
                steering_val = max(0, min(255, steering_val))
                data = bytes([steering_val])

                packet = self.create_packet(data, priority=0)  

                self.queue.put_nowait(packet)
                await self.event_bus.publish("ble.rx", {
                    "raw": steering_val,
                    "type": "STEERING_SIM",
                    "timestamp": asyncio.get_running_loop().time()
                })
            except Full:
                logger.warning("BLE queue full - dropping packet")
            except Exception as e:
                logger.error(f"BLE simulation error: {e}", exc_info=True)
            await asyncio.sleep(0.02)  

    async def start(self):
        if self.running:
            logger.debug("BLEReceiver already running")
            return

        self.running = True
        logger.info("Starting BLEReceiver")

        self._udp_task = asyncio.create_task(self._udp_forward_loop())
        self._simulate_task = asyncio.create_task(self.simulate())

    async def stop(self):
        if not self.running:
            return

        self.running = False
        logger.info("Stopping BLEReceiver")

        tasks = [t for t in [self._udp_task, self._simulate_task] if t and not t.done()]
        for t in tasks:
            t.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        if self._sock:
            self._sock.close()
            self._sock = None

        logger.info("BLEReceiver stopped")