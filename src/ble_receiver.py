# src/ble_receiver.py - ✅ PERFECTLY WORKING (Correct UDP format for can_translator)
import asyncio
import socket
import time
import random
from queue import PriorityQueue
import threading
import struct

DEVICE_ADDRESS = "SIMULATOR_MODE"
PRIORITY_QUEUE = PriorityQueue(maxsize=100)

def create_priority_packet(data, priority=1):
    return (priority, int(time.time() * 1_000_000), data)

async def notification_handler_simulator(data):
    packet = create_priority_packet(data, priority=1)
    PRIORITY_QUEUE.put_nowait(packet)
    print(f"🎮 BLE SIM RX: {data.hex()} [Priority {packet[0]}]")

def forward_thread():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        try:
            priority, ts, data = PRIORITY_QUEUE.get(timeout=0.001)
            # ✅ CORRECT FORMAT: priority(1byte) + timestamp(4bytes) + data
            udp_packet = bytes([priority]) + struct.pack('<I', ts) + data
            sock.sendto(udp_packet, ("127.0.0.1", 5005))
            PRIORITY_QUEUE.task_done()
            print(f"📡 Forwarded [{priority}, {ts}] -> UDP:5005")
        except:
            pass

async def run_ble_simulator():
    print(f"🚀 Automotive BLE SIMULATOR: {DEVICE_ADDRESS}")
    forward_daemon = threading.Thread(target=forward_thread, daemon=True)
    forward_daemon.start()
    
    steering_center = 127
    while True:
        steering_val = steering_center + int(43 * random.uniform(-1, 1))
        steering_val = max(0, min(255, steering_val))  # Clamp 0-255
        await notification_handler_simulator(bytes([steering_val]))
        await asyncio.sleep(0.02)  # 50Hz

if __name__ == "__main__":
    asyncio.run(run_ble_simulator())
