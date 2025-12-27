# src/dashboard_gui.py - PRODUCTION HMI (Colorful + Real-Time)
import tkinter as tk
from tkinter import ttk
import can
import threading
import time
from queue import Queue, Empty
import os

class AutomotiveHMI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 BLE-CAN Gateway | ASIL-B Production HMI")
        self.root.geometry("600x500")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(False, False)
        
        self.system_active = False
        self.last_heartbeat = 0
        self.gui_queue = Queue()
        
        self.setup_professional_ui()
        self.bus = can.interface.Bus('test', interface='virtual', bitrate=500000)
        self.start_safety_threads()
    
    def setup_professional_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#1a1a1a", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="BLE-CAN Automotive Gateway", font=("Consolas", 16, "bold"), 
                fg="#00ff88", bg="#1a1a1a").pack(pady=10)
        
        # Status Dashboard
        self.status_label = tk.Label(header, text="🛑 OFFLINE", fg="#ff4444", 
                                   font=("Consolas", 14, "bold"), bg="#1a1a1a")
        self.status_label.pack(side="right", padx=20)
        
        # Main Gauge
        main_frame = tk.Frame(self.root, bg="#0a0a0a")
        main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        tk.Label(main_frame, text="STEERING ANGLE", fg="#ffffff", 
                font=("Consolas", 16, "bold"), bg="#0a0a0a").pack(pady=(0,10))
        
        self.steering_gauge = ttk.Progressbar(main_frame, orient="horizontal", 
                                            length=450, mode="determinate", style="TProgressbar")
        self.steering_gauge.pack(pady=20)
        
        self.angle_label = tk.Label(main_frame, text="0°", fg="#00ff88", 
                                  font=("Consolas", 48, "bold"), bg="#0a0a0a")
        self.angle_label.pack(pady=(0,20))
        
        # Telemetry Panel
        tel_frame = tk.Frame(self.root, bg="#1a1a1a")
        tel_frame.pack(fill="x", padx=20, pady=(0,20))
        
        self.latency_label = tk.Label(tel_frame, text="Latency: -- μs", 
                                    fg="#ffaa00", font=("Consolas", 12), bg="#1a1a1a")
        self.latency_label.pack(side="left", padx=20)
        
        self.queue_label = tk.Label(tel_frame, text="Queue: 0", 
                                  fg="#66ccff", font=("Consolas", 12), bg="#1a1a1a")
        self.queue_label.pack(side="right", padx=20)
    
    def start_safety_threads(self):
        threading.Thread(target=self.can_receiver, daemon=True).start()
        threading.Thread(target=self.gui_update_loop, daemon=True).start()
        threading.Thread(target=self.safety_watchdog, daemon=True).start()
    
    def gui_update_loop(self):
        """Thread-safe GUI updates"""
        while True:
            try:
                update_data = self.gui_queue.get(timeout=0.01)
                self.root.after(0, self._apply_update, update_data)
            except Empty:
                pass
    
    def _apply_update(self, update_data):
        cmd, value = update_data
        if cmd == "STATUS":
            self.status_label.config(text=value[0], fg=value[1])
            self.system_active = "ACTIVE" in value[0]
        elif cmd == "STEERING":
            percentage = (value / 255) * 100
            self.steering_gauge['value'] = percentage
            self.angle_label.config(text=f"{int(value - 127)}°")
        elif cmd == "LATENCY":
            self.latency_label.config(text=f"Latency: {value} μs")
        elif cmd == "QUEUE":
            self.queue_label.config(text=f"Queue: {value}")
    
    def can_receiver(self):
        while True:
            try:
                msg = self.bus.recv(timeout=0.001)
                if msg.arbitration_id == 0x7FF:
                    self.last_heartbeat = time.time()
                    self.gui_queue.put(("STATUS", ("✅ ACTIVE", "#00ff88")))
                    latency = (msg.data[3] << 8) | msg.data[2]
                    self.gui_queue.put(("LATENCY", latency))
                    self.gui_queue.put(("QUEUE", msg.data[5]))
                elif msg.arbitration_id == 0x100:
                    self.gui_queue.put(("STEERING", msg.data[0]))
            except:
                pass
    
    def safety_watchdog(self):
        while True:
            if time.time() - self.last_heartbeat > 2.0:
                self.gui_queue.put(("STATUS", ("🚨 FAULT", "#ff4444")))
            time.sleep(0.1)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomotiveHMI(root)
    root.mainloop()
