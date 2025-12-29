import can
import time
import socket
import csv
import threading
import struct
from queue import PriorityQueue, Empty, Full
import os
import math

class CANTranslator:
    def __init__(self):
        self.start_time = time.time()
        os.makedirs("data", exist_ok=True)
        self.log_file = "data/telemetry_log.csv"
        self.priority_queue = PriorityQueue(maxsize=200)
        self.running = True
        self.sock = None

    def scale_steering(self, raw):
        """0-255 raw → -450° to +450° vehicle steering angle"""
        return int((raw - 127) * (900 / 255))

    def build_can_message(self, steering_angle, priority, ts_us):
        ts_bytes = struct.pack('<Q', ts_us)[:5]
        angle_bytes = struct.pack('<h', steering_angle)  
        return bytearray(angle_bytes + bytes([priority]) + ts_bytes)

    def process_packet(self, item):
        priority, ts_us, ble_data = item
        raw = ble_data[0] if ble_data else 127
        steering_angle = self.scale_steering(raw)

        can_data = self.build_can_message(steering_angle, priority, ts_us)
        msg = can.Message(arbitration_id=0x100, data=can_data, is_extended_id=False)

        try:
            t0 = time.perf_counter()
            self.bus.send(msg, timeout=0.002)
            latency_us = int((time.perf_counter() - t0) * 1_000_000)

            with open(self.log_file, "a", newline="", buffering=1) as f:
                csv.writer(f).writerow([
                    time.time(), steering_angle, latency_us, priority, self.priority_queue.qsize()
                ])

            print(f"\r Steering: {steering_angle:4}° {latency_us:3}μs", end="")

        except can.CanError:
            print("\n CAN BUS FAIL: retry later")

    def can_forward_thread(self):
        while self.running:
            try:
                packet = self.priority_queue.get(timeout=0.01)
                self.process_packet(packet)
                self.priority_queue.task_done()
            except Empty:
                pass

    def udp_receiver_thread(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(64)
                if len(data) >= 10:  
                    priority = data[0]
                    ts_us = struct.unpack('<Q', data[1:9])[0]
                    payload = data[9:]

                    try:
                        self.priority_queue.put_nowait((priority, ts_us, payload))
                    except Full:
                        print(" Queue Overflow: dropping sample")
            except:
                pass

    def send_heartbeat_thread(self):
        while self.running:
            uptime = int(time.time() - self.start_time)
            queue_depth = self.priority_queue.qsize()
            hb = struct.pack('<B H B 4x', 0x01, uptime & 0xFFFF, queue_depth)
            self.bus.send(can.Message(arbitration_id=0x7FF, data=hb))
            time.sleep(1)

    def shutdown(self):
        self.running = False
        time.sleep(0.1)
        if self.sock:
            self.sock.close()
        print("\n CAN Gateway Down")

def main():
    print(" CAN Translator Starting...")
    tr = CANTranslator()
    tr.bus = can.interface.Bus(interface='virtual', channel='vcan0')
    print(" CAN Bus Linked (vcan0)")

    tr.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tr.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tr.sock.bind(("127.0.0.1", 5005))
    print(" UDP Receiver Ready @ 5005")

    threading.Thread(target=tr.udp_receiver_thread, daemon=True).start()
    threading.Thread(target=tr.can_forward_thread, daemon=True).start()
    threading.Thread(target=tr.send_heartbeat_thread, daemon=True).start()

    print(" BLE → UDP → CAN Pipeline Active\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        tr.shutdown()

if __name__ == "__main__":
    main()
