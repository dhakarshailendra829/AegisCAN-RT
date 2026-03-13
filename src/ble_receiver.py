"""
BLE to UDP packet forwarding with simulation support.

Features:
- Priority queue packet buffering
- UDP packet transmission
- Steering data simulation
- Graceful task management
- Exception isolation
"""

import asyncio
import logging
import socket
import struct
import random
from queue import PriorityQueue, Full, Empty
from typing import Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from core.event_bus import event_bus, EventTopic

logger = logging.getLogger(__name__)

# Configuration constants
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
STEERING_CENTER = 127
STEERING_RANGE = 55  # +/- degrees
STEERING_MIN = 0
STEERING_MAX = 255
PACKET_TIMEOUT = 0.1
SIMULATE_INTERVAL = 0.02  # 50 Hz


@dataclass
class PacketInfo:
    """Information about a BLE packet."""
    priority: int
    timestamp_us: int
    data: bytes
    received_at: datetime


class BLEReceiver:
    """
    Receives BLE data and forwards via UDP with priority queue buffering.

    Features:
    - Priority queue packet management
    - UDP socket communication
    - Steering data simulation
    - Exception handling and recovery
    - Graceful shutdown
    """

    def __init__(self, max_queue_size: int = 500):
        """
        Initialize BLE receiver.

        Args:
            max_queue_size: Maximum queue size
        """
        self.queue: PriorityQueue = PriorityQueue(maxsize=max_queue_size)
        self.running = False
        self._udp_task: Optional[asyncio.Task] = None
        self._simulate_task: Optional[asyncio.Task] = None
        self._sock: Optional[socket.socket] = None
        self._logger = logging.getLogger(__name__)
        self._packet_count = 0
        self._drop_count = 0

    def create_packet(
        self,
        data: bytes,
        priority: int = 1
    ) -> Tuple[int, int, bytes]:
        """
        Create a timestamped packet.

        Args:
            data: Packet data
            priority: Packet priority

        Returns:
            tuple: (priority, timestamp_us, data)
        """
        ts_us = int(asyncio.get_running_loop().time() * 1_000_000)
        return priority, ts_us, data

    async def _udp_forward_loop(self) -> None:
        """Forward queued packets via UDP."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            self._logger.info(f"UDP forward starting: {UDP_IP}:{UDP_PORT}")

            while self.running:
                try:
                    # Get packet from queue with timeout
                    priority, ts, data = await asyncio.wait_for(
                        asyncio.to_thread(self.queue.get_nowait),
                        timeout=PACKET_TIMEOUT
                    )

                    # Pack: [priority(1byte)][timestamp(8bytes)][data(remaining)]
                    packet = bytes([priority]) + struct.pack('<Q', ts) + data

                    # Send via UDP
                    self._sock.sendto(packet, (UDP_IP, UDP_PORT))
                    self._packet_count += 1

                    # Publish telemetry event
                    await event_bus.publish(
                        EventTopic.BLE_TX.value,
                        {
                            "priority": priority,
                            "timestamp_us": ts,
                            "data_len": len(data),
                            "packet_number": self._packet_count
                        }
                    )

                    self._logger.debug(
                        f"UDP packet sent: priority={priority}, len={len(data)}"
                    )

                except asyncio.TimeoutError:
                    # No packet available
                    continue

                except Full:
                    self._drop_count += 1
                    self._logger.warning(
                        f"Queue full - dropped {self._drop_count} packets total"
                    )
                    await asyncio.sleep(0.01)

                except Exception as e:
                    self._logger.error(f"UDP forward error: {e}", exc_info=True)
                    await asyncio.sleep(0.5)

        except Exception as e:
            self._logger.error(f"UDP forward loop failed: {e}", exc_info=True)

        finally:
            if self._sock:
                self._sock.close()
                self._sock = None
            self._logger.info(
                f"UDP forward loop ended (sent={self._packet_count}, "
                f"dropped={self._drop_count})"
            )

    async def simulate(self) -> None:
        """Simulate steering data input."""
        self._logger.info("BLE simulation starting")

        while self.running:
            try:
                # Generate realistic steering angle variation
                steering_val = int(
                    STEERING_CENTER + STEERING_RANGE * random.uniform(-1, 1)
                )
                steering_val = max(STEERING_MIN, min(STEERING_MAX, steering_val))
                data = bytes([steering_val])

                # Create and queue packet
                packet = self.create_packet(data, priority=0)

                try:
                    self.queue.put_nowait(packet)

                    # Publish BLE RX event
                    await event_bus.publish(
                        EventTopic.BLE_RX.value,
                        {
                            "raw": steering_val,
                            "type": "STEERING_SIM",
                            "timestamp": asyncio.get_running_loop().time(),
                            "range": (STEERING_MIN, STEERING_MAX)
                        }
                    )

                    self._logger.debug(f"BLE simulated: steering={steering_val}")

                except Full:
                    self._drop_count += 1
                    self._logger.warning("BLE queue full - dropping packet")

                await asyncio.sleep(SIMULATE_INTERVAL)

            except Exception as e:
                self._logger.error(f"BLE simulation error: {e}", exc_info=True)
                await asyncio.sleep(0.1)

        self._logger.info("BLE simulation stopped")

    async def start(self) -> None:
        """Start BLE receiver and simulator."""
        if self.running:
            self._logger.warning("BLEReceiver already running")
            return

        self.running = True
        self._logger.info("Starting BLEReceiver")

        # Start background tasks
        self._udp_task = asyncio.create_task(self._udp_forward_loop())
        self._simulate_task = asyncio.create_task(self.simulate())

        self._logger.info("BLEReceiver started successfully")

    async def stop(self) -> None:
        """Stop BLE receiver and simulator gracefully."""
        if not self.running:
            return

        self.running = False
        self._logger.info("Stopping BLEReceiver")

        # Cancel all tasks
        tasks = [t for t in [self._udp_task, self._simulate_task] if t and not t.done()]

        for task in tasks:
            task.cancel()

        # Wait for cancellation
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self._logger.info(f"BLEReceiver stopped (packets={self._packet_count})")

    def health_status(self) -> dict:
        """Get receiver health status."""
        return {
            "running": self.running,
            "queue_size": self.queue.qsize(),
            "packets_sent": self._packet_count,
            "packets_dropped": self._drop_count
        }