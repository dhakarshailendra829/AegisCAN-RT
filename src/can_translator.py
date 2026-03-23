"""
UDP to CAN frame translation with attack simulation.

Features:
- Real-time UDP packet reception
- CAN frame generation and transmission
- Steering angle scaling
- Attack mode injection
- Latency measurement
- Error recovery
"""

import asyncio
import logging
import socket
import struct
import time
from queue import PriorityQueue, Empty
from typing import Optional, Tuple
from dataclasses import dataclass

try:
    import can
except ImportError:
    can = None
from core.event_bus import event_bus, EventTopic

logger = logging.getLogger(__name__)

CAN_INTERFACE_PRIORITY = ["virtual", "socketcan"]  
CAN_CHANNEL = "vcan0"
CAN_ARBITRATION_ID = 0x100
STEERING_SCALE_FACTOR = 900 / 255  
UDP_LISTEN_IP = "127.0.0.1"
UDP_LISTEN_PORT = 5005

@dataclass
class PacketMetrics:
    priority: int
    timestamp_us: int
    steering_angle: int
    latency_us: int
    queue_size: int
    attack_mode: Optional[str] = None


class CANTranslator:
    def __init__(self, attack_mode: Optional[str] = None):
        self.queue: PriorityQueue = PriorityQueue(maxsize=500)
        self.running = False
        self.attack_mode = attack_mode
        self.can_bus: Optional[can.Bus] = None
        self._udp_task: Optional[asyncio.Task] = None
        self._process_task: Optional[asyncio.Task] = None
        self._sock: Optional[socket.socket] = None
        self._logger = logging.getLogger(__name__)
        self._packet_count = 0
        self._error_count = 0

    def _setup_can_bus(self) -> None:
        if can is None:
            self._logger.warning("python-can not installed - CAN disabled")
            return

        for interface in CAN_INTERFACE_PRIORITY:
            try:
                self.can_bus = can.interface.Bus(
                    interface=interface,
                    channel=CAN_CHANNEL,
                    receive_own_messages=True
                )
                self._logger.info(f"CAN bus initialized: {interface}")
                return
            except Exception as e:
                self._logger.debug(f"Failed to initialize {interface}: {e}")
                continue

        raise RuntimeError("Failed to initialize CAN bus on any interface")

    def _scale_steering(self, raw: int) -> int:
        return int((raw - 127) * STEERING_SCALE_FACTOR)

    async def _udp_receiver_loop(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((UDP_LISTEN_IP, UDP_LISTEN_PORT))
        self._sock.setblocking(False)

        loop = asyncio.get_running_loop()

        self._logger.info(f"UDP receiver listening on {UDP_LISTEN_IP}:{UDP_LISTEN_PORT}")

        try:
            while self.running:
                try:
                    data, _ = await loop.sock_recvfrom(self._sock, 64)

                    if len(data) >= 10:
                        priority = data[0]
                        ts_us = struct.unpack('<Q', data[1:9])[0]
                        ble_data = data[9:]

                        try:
                            await asyncio.to_thread(
                                self.queue.put_nowait,
                                (priority, ts_us, ble_data)
                            )
                            self._logger.debug(
                                f"UDP packet queued: priority={priority}, "
                                f"len={len(ble_data)}"
                            )
                        except Exception as e:
                            self._logger.warning(f"Queue error: {e}")

                except BlockingIOError:
                    await asyncio.sleep(0.005)

                except Exception as e:
                    self._error_count += 1
                    self._logger.error(f"UDP receive error: {e}", exc_info=True)
                    await asyncio.sleep(0.5)

        finally:
            if self._sock:
                self._sock.close()
                self._sock = None
            self._logger.info("UDP receiver loop ended")

    def _process_packet(self, item: Tuple[int, int, bytes]) -> None:
        priority, ts_us, ble_data = item

        try:
            raw = ble_data[0] if ble_data else 127
            steering_angle = self._scale_steering(raw)

            if self.attack_mode == "flip":
                steering_angle = -steering_angle
            elif self.attack_mode == "dos":
                time.sleep(0.05)  
            elif self.attack_mode == "heart":
                return  

            can_data = struct.pack('<h', steering_angle)
            msg = can.Message(
                arbitration_id=CAN_ARBITRATION_ID,
                data=can_data,
                is_extended_id=False
            )

            t0 = time.perf_counter()

            if self.can_bus:
                self.can_bus.send(msg)

            latency_us = int((time.perf_counter() - t0) * 1_000_000)
            self._packet_count += 1

            asyncio.create_task(
                event_bus.publish(
                    EventTopic.CAN_TX.value,
                    {
                        "angle": steering_angle,
                        "latency_us": latency_us,
                        "queue_size": self.queue.qsize(),
                        "timestamp_us": ts_us,
                        "attack_mode": self.attack_mode,
                        "packet_number": self._packet_count
                    }
                )
            )

            self._logger.debug(
                f"CAN TX: angle={steering_angle}°, latency={latency_us}µs"
            )

        except Exception as e:
            self._error_count += 1
            self._logger.error(f"CAN packet processing failed: {e}", exc_info=True)

    async def _process_loop(self) -> None:
        self._logger.info("CAN process loop started")

        while self.running:
            try:
                packet = await asyncio.wait_for(
                    asyncio.to_thread(self.queue.get_nowait),
                    timeout=0.1
                )
                self._process_packet(packet)

            except asyncio.TimeoutError:
                await asyncio.sleep(0.005)

            except Empty:
                await asyncio.sleep(0.005)

            except Exception as e:
                self._error_count += 1
                self._logger.error(f"Process loop error: {e}", exc_info=True)
                await asyncio.sleep(0.5)

        self._logger.info("CAN process loop ended")

    async def start(self) -> None:
        if self.running:
            self._logger.warning("CANTranslator already running")
            return

        try:
            self._setup_can_bus()
        except Exception as e:
            self._logger.error(f"Failed to setup CAN bus: {e}")
            raise

        self.running = True
        self._logger.info(f"Starting CANTranslator (attack_mode={self.attack_mode})")

        self._udp_task = asyncio.create_task(self._udp_receiver_loop())
        self._process_task = asyncio.create_task(self._process_loop())

        self._logger.info("CANTranslator started successfully")

    async def stop(self) -> None:
        if not self.running:
            return

        self.running = False
        self._logger.info("Stopping CANTranslator")

        tasks = [t for t in [self._udp_task, self._process_task] if t and not t.done()]

        for task in tasks:
            task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        if self.can_bus:
            self.can_bus.shutdown()
            self.can_bus = None

        self._logger.info(
            f"CANTranslator stopped (packets={self._packet_count}, "
            f"errors={self._error_count})"
        )

    def health_status(self) -> dict:
        return {
            "running": self.running,
            "attack_mode": self.attack_mode,
            "queue_size": self.queue.qsize(),
            "packets_processed": self._packet_count,
            "errors": self._error_count,
            "can_available": self.can_bus is not None
        }