import can
import time
import socket
import threading
import struct
import json
from queue import PriorityQueue, Empty
from core.event_bus import EventBus

class CANTranslator:

    def __init__(self, event_bus: EventBus):

        self.bus = event_bus
        self.queue = PriorityQueue(maxsize=500)
        self.running = True

    def scale_steering(self, raw):
        return int((raw - 127) * (900 / 255))

    def setup_bus(self):

        try:
            self.can_bus = can.interface.Bus(interface='virtual', channel='vcan0')
        except:
            self.can_bus = can.interface.Bus(interface='socketcan', channel='vcan0')

    def udp_receiver(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # allow reuse port (streamlit restart fix)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(("127.0.0.1", 5005))

        while self.running:
            try:
                data, _ = sock.recvfrom(64)

                if len(data) >= 10:
                    priority = data[0]
                    ts_us = struct.unpack('<Q', data[1:9])[0]
                    self.queue.put_nowait((priority, ts_us, data[9:]))

            except:
                continue


    def process_packet(self, item):

        priority, ts_us, ble_data = item

        raw = ble_data[0] if ble_data else 127
        steering_angle = self.scale_steering(raw)
        # fake attack impact simulation
        if hasattr(self, "attack_mode"):

            if self.attack_mode == "flip":
                steering_angle = -steering_angle

            elif self.attack_mode == "dos":
                time.sleep(0.05)

            elif self.attack_mode == "heart":
                return

        can_data = struct.pack('<h', steering_angle)
        msg = can.Message(arbitration_id=0x100, data=can_data, is_extended_id=False)

        t0 = time.perf_counter()
        self.can_bus.send(msg)
        latency = int((time.perf_counter()-t0)*1_000_000)

        self.bus.publish("can.tx", {
            "angle": steering_angle,
            "latency": latency,
            "queue": self.queue.qsize()
        })

    def run(self):

        self.setup_bus()

        threading.Thread(target=self.udp_receiver, daemon=True).start()

        while self.running:
            try:
                packet = self.queue.get(timeout=0.01)
                self.process_packet(packet)
            except Empty:
                continue

    def stop(self):
        self.running = False
