import tkinter as tk
from tkinter import ttk
import threading
import time
import can
from queue import Queue, Empty
import math
import struct

class AutomotiveHMI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automotive Gateway Dashboard")
        self.root.geometry("600x650")
        self.root.configure(bg="#121212")
        self.root.resizable(False, False)

        self.last_heartbeat = 0
        self.gui_queue = Queue()
        self.current_angle = 0  

        self.setup_modern_styles()
        self.create_widgets()

        try:
            self.bus = can.interface.Bus(interface='virtual', channel='vcan0')
            print("HMI linked to vcan0")
        except Exception as e:
            print(f" HMI Bus Error: {e}")
            return

        self.start_threads()

    def setup_modern_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Horizontal.TProgressbar", thickness=15, troughcolor='#1a1a1a', background='#00ff88')

    def create_widgets(self):
        header = tk.Frame(self.root, bg="#1a1a1a", height=80)
        header.pack(fill="x")

        tk.Label(header, text="GATEWAY TELEMETRY", font=("Segoe UI", 18, "bold"),
                 fg="#00ff88", bg="#1a1a1a").pack(side="left", padx=20)

        self.status_label = tk.Label(header, text="● OFFLINE", fg="#ff4444", 
                                     font=("Segoe UI", 14, "bold"), bg="#1a1a1a")
        self.status_label.pack(side="right", padx=20)

        self.canvas = tk.Canvas(self.root, width=400, height=300,
                                bg="#121212", highlightthickness=0)
        self.canvas.pack(pady=20)
        self.canvas.create_arc(50, 50, 350, 350, start=180,
                               extent=-180, style="arc",
                               outline="#333", width=20)

        self.canvas.create_text(200, 160, text="STEERING", fill="#666",
                                font=("Segoe UI", 10, "bold"))

        self.angle_label = tk.Label(self.root, text="0°", fg="#00ff88",
                                    font=("Segoe UI", 60, "bold"), bg="#121212")
        self.angle_label.pack()

        self.needle = self.canvas.create_line(200, 200, 200, 100,
                                             fill="#ff9800", width=5)

        tel_frame = tk.Frame(self.root, bg="#1a1a1a", height=140)
        tel_frame.pack(fill="x", side="bottom")

        self.latency_label = tk.Label(tel_frame, text="⚡ Latency: -- μs",
                                      fg="#ffaa00", font=("Consolas", 14, "bold"),
                                      bg="#1a1a1a")
        self.latency_label.pack(pady=6)

        self.queue_label = tk.Label(tel_frame, text="📊 Queue: 0 Frames",
                                    fg="#66ccff", font=("Consolas", 12),
                                    bg="#1a1a1a")
        self.queue_label.pack(pady=4)

    def update_needle(self, steering_angle):
        alpha = 0.25  
        self.current_angle = (alpha * steering_angle +
                              (1 - alpha) * self.current_angle)

        angle_rad = math.radians(self.current_angle - 90)
        x = 200 + 120 * math.cos(angle_rad)
        y = 200 + 120 * math.sin(angle_rad)
        self.canvas.coords(self.needle, 200, 200, x, y)

        self.angle_label.config(text=f"{int(self.current_angle)}°")

    def start_threads(self):
        threading.Thread(target=self.can_receiver, daemon=True).start()
        threading.Thread(target=self.gui_update_loop, daemon=True).start()
        threading.Thread(target=self.heartbeat_watchdog, daemon=True).start()

    def gui_update_loop(self):
        while True:
            try:
                key, value = self.gui_queue.get(timeout=0.01)
                if key == "STATUS": self.status_label.config(text=value[0], fg=value[1])
                elif key == "ANGLE": self.update_needle(value)
                elif key == "LAT": self.latency_label.config(text=f"Latency: {value} μs")
                elif key == "Q": self.queue_label.config(text=f"Queue: {value} Frames")
            except Empty:
                pass

    def can_receiver(self):
        while True:
            msg = self.bus.recv(timeout=0.05)
            if not msg: continue

            if msg.arbitration_id == 0x7FF:
                self.last_heartbeat = time.time()
                q_depth = msg.data[2]  
                self.gui_queue.put(("STATUS", ("● ACTIVE", "#00ff88")))
                self.gui_queue.put(("Q", q_depth))

            elif msg.arbitration_id == 0x100:
                steering_angle = struct.unpack('<h', msg.data[0:2])[0]
                self.gui_queue.put(("ANGLE", steering_angle))

                self.gui_queue.put(("LAT", "--"))

    def heartbeat_watchdog(self):
        while True:
            if time.time() - self.last_heartbeat > 2:
                self.gui_queue.put(("STATUS", ("● FAULT", "#ff4444")))
            time.sleep(0.5)

if __name__ == "__main__":
    root = tk.Tk()
    AutomotiveHMI(root)
    root.mainloop()
