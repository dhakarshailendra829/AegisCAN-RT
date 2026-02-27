# src/can_translator.py
import asyncio
import time
import socket
import struct
from queue import PriorityQueue, Empty

import can

from core.logger_engine import logger
from core.event_bus import event_bus
from core.task_manager import task_manager


class CANTranslator:
    """Translates BLE/UDP packets to CAN messages with attack simulation support."""

    def __init__(self, event_bus=event_bus, attack_mode: str | None = None):
        self.event_bus = event_bus
        self.queue = PriorityQueue(maxsize=500)
        self.running = False
        self.attack_mode = attack_mode
        self.can_bus: can.interface.Bus | None = None
        self._udp_task: asyncio.Task | None = None
        self._process_task: asyncio.Task | None = None

    def scale_steering(self, raw: int) -> int:
        """Scale BLE 0-255 value to CAN steering angle range (-900 to +900)."""
        return int((raw - 127) * (900 / 255))

    def _setup_can_bus(self):
        """Initialize virtual or socketcan bus."""
        try:
            self.can_bus = can.interface.Bus(interface='virtual', channel='vcan0', receive_own_messages=True)
            logger.info("CAN bus initialized: virtual (vcan0)")
        except Exception:
            try:
                self.can_bus = can.interface.Bus(interface='socketcan', channel='vcan0')
                logger.info("CAN bus initialized: socketcan (vcan0)")
            except Exception as e:
                logger.error(f"Failed to initialize CAN bus: {e}", exc_info=True)
                raise

    async def _udp_receiver_loop(self):
        """Async UDP listener for incoming BLE packets."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 5005))
        sock.setblocking(False)

        loop = asyncio.get_running_loop()

        try:
            while self.running:
                try:
                    data, _ = await loop.sock_recvfrom(sock, 64)
                    if len(data) >= 10:
                        priority = data[0]
                        ts_us = struct.unpack('<Q', data[1:9])[0]
                        await asyncio.to_thread(self.queue.put_nowait, (priority, ts_us, data[9:]))
                        logger.debug(f"Received UDP packet: priority={priority}, len={len(data[9:])}")
                except BlockingIOError:
                    await asyncio.sleep(0.005)
                except Exception as e:
                    logger.error(f"UDP receive error: {e}", exc_info=True)
                    await asyncio.sleep(0.5)
        finally:
            sock.close()
            logger.info("UDP receiver loop ended")

    def process_packet(self, item: tuple[int, int, bytes]):
        """Process one packet: apply attack → send CAN message."""
        priority, ts_us, ble_data = item
        raw = ble_data[0] if ble_data else 127
        steering_angle = self.scale_steering(raw)

        # Apply active attack
        if self.attack_mode == "flip":
            steering_angle = -steering_angle
        elif self.attack_mode == "dos":
            time.sleep(0.05)  # simulated delay
        elif self.attack_mode == "heart":
            return  # drop heartbeat-like message

        can_data = struct.pack('<h', steering_angle)
        msg = can.Message(arbitration_id=0x100, data=can_data, is_extended_id=False)

        t0 = time.perf_counter()
        try:
            self.can_bus.send(msg)
            latency_us = int((time.perf_counter() - t0) * 1_000_000)

            asyncio.create_task(self.event_bus.publish("can.tx", {
                "angle": steering_angle,
                "latency_us": latency_us,
                "queue_size": self.queue.qsize(),
                "timestamp_us": ts_us,
                "type": "CAN_TX"
            }))
            logger.debug(f"CAN message sent: angle={steering_angle}, latency={latency_us}us")
        except Exception as e:
            logger.error(f"CAN send failed: {e}", exc_info=True)

    async def _process_loop(self):
        """Async packet processing loop."""
        while self.running:
            try:
                packet = await asyncio.wait_for(
                    asyncio.to_thread(self.queue.get_nowait),
                    timeout=0.1
                )
                self.process_packet(packet)
            except (asyncio.TimeoutError, Empty):
                await asyncio.sleep(0.005)  # silent idle
            except Exception as e:
                logger.error(f"Packet processing error: {e}", exc_info=True)
                await asyncio.sleep(0.5)

    async def start(self):
        if self.running:
            logger.debug("CANTranslator already running")
            return

        self.running = True
        logger.info(f"Starting CANTranslator (attack_mode={self.attack_mode})")

        self._setup_can_bus()

        self._udp_task = asyncio.create_task(self._udp_receiver_loop())
        self._process_task = asyncio.create_task(self._process_loop())

    async def stop(self):
        if not self.running:
            return

        self.running = False
        logger.info("Stopping CANTranslator")

        tasks = [t for t in [self._udp_task, self._process_task] if t and not t.done()]
        for t in tasks:
            t.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        if self.can_bus:
            try:
                self.can_bus.shutdown()
            except Exception as e:
                logger.error(f"CAN bus shutdown failed: {e}")

        logger.info("CANTranslator stopped")