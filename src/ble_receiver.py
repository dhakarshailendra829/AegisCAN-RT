import asyncio
import socket
import time
import random
import threading
import struct
import json
from queue import PriorityQueue, Full
from core.event_bus import EventBus

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

class BLEReceiver:

    def __init__(self, event_bus: EventBus):
        self.queue = PriorityQueue(maxsize=500)
        self.exit_event = threading.Event()
        self.bus = event_bus

    def create_packet(self, data, priority=1):
        return (priority, int(time.time()*1_000_000), data)

    def forward_thread(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while not self.exit_event.is_set():
            try:
                priority, ts, data = self.queue.get(timeout=0.01)
                packet = bytes([priority]) + struct.pack('<Q', ts) + data
                sock.sendto(packet, (UDP_IP, UDP_PORT))

                self.bus.publish("ble.tx", {
                    "priority": priority,
                    "timestamp": ts
                })

            except:
                continue
        sock.close()

    async def simulate(self):

        threading.Thread(target=self.forward_thread, daemon=True).start()

        steering_center = 127

        while not self.exit_event.is_set():

            steering_val = steering_center + int(55 * random.uniform(-1,1))
            steering_val = max(0, min(255, steering_val))

            data = bytes([steering_val])
            packet = self.create_packet(data, priority=0)

            try:
                self.queue.put_nowait(packet)

                self.bus.publish("ble.rx", {
                    "raw": steering_val,
                    "type": "BLE_RX"
                })

            except Full:
                pass

            await asyncio.sleep(0.02)

    def start(self):
        asyncio.run(self.simulate())

    def stop(self):
        self.exit_event.set()
