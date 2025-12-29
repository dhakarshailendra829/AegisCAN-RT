import can
import time
import statistics
import socket
import struct
import csv
import os


class LatencyValidator:
    def __init__(self):
        try:
            self.bus = can.interface.Bus(channel='virtual_ch', interface='virtual')
            print(" Connected to CAN bus (virtual_ch)")
        except Exception as e:
            print(f" CAN INIT ERROR: {e}")
            exit(1)

        self.results = []
        os.makedirs("data", exist_ok=True)

    def send_test_frame(self, steering_val):
        """Send BLE-style UDP packet → CAN pipeline"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ts_us = int(time.time() * 1_000_000) & 0xFFFFFFFF

        packet = bytes([1]) + struct.pack('<I', ts_us) + bytes([steering_val])
        sock.sendto(packet, ("127.0.0.1", 5005))
        sock.close()

    def run_benchmark(self, count=300):
        print(f"\nStarting Latency Benchmark ({count} frames)...")

        for i in range(count):
            val = (i * 3) % 255
            self.send_test_frame(val)

            msg = self.bus.recv(timeout=0.1)
            if msg and msg.arbitration_id == 0x100:
                low = msg.data[2]
                high = msg.data[3]
                latency_us = (high << 8) | low

                if latency_us > 0:
                    self.results.append(latency_us)

            time.sleep(0.003)

        self.report_results()

    def report_results(self):
        if not self.results:
            print("\n Test Failed: No latency data received.")
            print(" Ensure can_translator.py is running!")
            return

        ms = [x / 1000 for x in self.results]

        avg  = statistics.mean(ms)
        p99  = statistics.quantiles(ms, n=100)[98]
        stdv = statistics.stdev(ms) if len(ms) > 1 else 0

        print("\n==============================")
        print("LATENCY PERFORMANCE REPORT")
        print(f"Samples: {len(ms)}")
        print(f"AVG Latency: {avg:.3f} ms")
        print(f"P99 Latency: {p99:.3f} ms")
        print(f"Jitter (StdDev): {stdv:.3f} ms")
        print("==============================")

        out = "data/latency_analysis.csv"
        with open(out, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Sample", "Latency(ms)"])
            for i, v in enumerate(ms):
                w.writerow([i, v])

        print(f"Results stored at: {out}")


if __name__ == "__main__":
    LatencyValidator().run_benchmark()
