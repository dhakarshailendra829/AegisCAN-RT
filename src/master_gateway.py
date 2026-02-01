import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import subprocess
import time
import queue
import os
import psutil
import platform

SERVICES = {
    "BLE_SIM": ["python", "src/ble_receiver.py"],
    "CAN_GW": ["python", "src/can_translator.py"],
    "HMI": ["python", "src/dashboard_gui.py"]
}

class EnterpriseGatewayUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BLE-CAN Production Gateway")
        self.root.geometry("1100x800")
        self.root.configure(bg="#0d1117")

        self.processes = {}
        self.log_queue = queue.Queue()
        self.start_time = None

        self.setup_enterprise_ui()

        threading.Thread(target=self.log_display_loop, daemon=True).start()
        threading.Thread(target=self.system_monitor_loop, daemon=True).start()
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()

    def setup_enterprise_ui(self):
        # Title Frame
        title_frame = tk.Frame(self.root, bg="#161b22", height=90)
        title_frame.pack(fill="x")
        lbl_title = tk.Label(title_frame, text="AUTOMOTIVE GATEWAY CONTROL",
                             font=("Segoe UI", 22, "bold"),
                             fg="#58a6ff", bg="#161b22")
        lbl_title.pack(side="left", padx=30, pady=20)

        self.status_led = tk.Canvas(title_frame, width=26, height=26,
                                    bg="#161b22", highlightthickness=0)
        self.status_led.pack(side="right", padx=20)
        self.led_circle = self.status_led.create_oval(5, 5, 21, 21, fill="#f85149")

        # Control Frame
        control_frame = tk.Frame(self.root, bg="#0d1117")
        control_frame.pack(fill="x", padx=30, pady=20)

        tk.Button(control_frame, text="LAUNCH PRODUCTION",
                  command=self.start_production,
                  bg="#238636", fg="white",
                  font=("Segoe UI", 12, "bold"),
                  width=22, height=2).grid(row=0, column=0, padx=10)

        tk.Button(control_frame, text="VALIDATION SUITE",
                  command=self.run_tests,
                  bg="#9e6a03", fg="white",
                  font=("Segoe UI", 12, "bold"),
                  width=20, height=2).grid(row=0, column=1, padx=10)

        tk.Button(control_frame, text="SYSTEM STOP",
                  command=self.stop_all,
                  bg="#da3633", fg="white",
                  font=("Segoe UI", 12, "bold"),
                  width=20, height=2).grid(row=0, column=2, padx=10)

        # Metrics Tiles
        metrics = tk.Frame(self.root, bg="#0d1117")
        metrics.pack(fill="x", padx=30)

        self.lat_tile = tk.Label(metrics, text="LATENCY: -- ms",
                                 bg="#161b22", fg="#ffa657",
                                 font=("Consolas", 14, "bold"), width=22, pady=15)
        self.lat_tile.pack(side="left", padx=10)

        self.up_tile = tk.Label(metrics, text="UPTIME: 00:00",
                                bg="#161b22", fg="#79c0ff",
                                font=("Consolas", 14, "bold"), width=22, pady=15)
        self.up_tile.pack(side="left", padx=10)

        self.sys_tile = tk.Label(metrics, text="CPU: --% | RAM: --%",
                                 bg="#161b22", fg="#3fb950",
                                 font=("Consolas", 14, "bold"), width=26, pady=15)
        self.sys_tile.pack(side="right", padx=10)

        # ✅ Simulation Mode Label
        self.sim_mode_label = tk.Label(metrics, text="", bg="#0d1117", fg="#ffa657",
                                       font=("Consolas", 12, "bold"), width=30)
        self.sim_mode_label.pack(side="right", padx=10)
        if platform.system() == "Windows":
            self.sim_mode_label.config(text="Simulation Mode (Windows)")

        # Log Container
        log_container = tk.Frame(self.root, bg="#161b22", bd=1)
        log_container.pack(fill="both", expand=True, padx=40, pady=10)
        self.log_text = scrolledtext.ScrolledText(
            log_container, bg="#0d1117", fg="#c9d1d9",
            font=("Consolas", 11), borderwidth=0
        )
        self.log_text.pack(fill="both", expand=True)

    # Logging
    def log(self, message):
        self.log_queue.put(f"[{time.strftime('%H:%M:%S')}] {message}\n")

    def log_display_loop(self):
        while True:
            try:
                msg = self.log_queue.get(timeout=0.1)
                self.log_text.insert(tk.END, msg)
                self.log_text.see(tk.END)
            except:
                pass

    # Start Production
    def start_production(self):
        if self.start_time: return
        self.start_time = time.time()
        self.status_led.itemconfig(self.led_circle, fill="#3fb950")
        self.log("Production Gateway Online")

        for name, cmd in SERVICES.items():
            self.start_service(name, cmd)
            time.sleep(0.4)

        # Windows-safe: skip latency benchmark if running on Windows
        if platform.system() == "Windows":
            self.log("⚠️ Windows detected: Skipping latency benchmark in simulation mode")
        else:
            # Linux / real CAN: run latency benchmark if available
            try:
                import master_gateway  # Ensure this exists
                master_gateway.run_latency_benchmark()
            except Exception as e:
                self.log(f"Latency benchmark skipped / failed: {e}")

    # Start individual service
    def start_service(self, name, cmd):
        try:
            creation_flag = subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, creationflags=creation_flag
            )
            self.processes[name] = proc
            self.log(f" {name} launched (PID={proc.pid})")
        except Exception as e:
            self.log(f" {name} failed: {e}")

    # System Monitor
    def system_monitor_loop(self):
        while True:
            if not self.start_time: 
                time.sleep(1)
                continue
            uptime = int(time.time() - self.start_time)
            self.up_tile.config(text=f"UPTIME: {uptime//60:02}:{uptime%60:02}")
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.sys_tile.config(text=f"CPU: {cpu}% | RAM: {ram}%")
            time.sleep(1)

    # Heartbeat / Auto Restart
    def heartbeat_loop(self):
        while True:
            for name, proc in list(self.processes.items()):
                if proc.poll() is not None:  
                    self.log(f"🔁 RESTARTING {name} (Crash Detected)")
                    self.start_service(name, SERVICES[name])
            time.sleep(2)

    # Run Tests
    def run_tests(self):
        self.log(" Running Validation Suite...")
        threading.Thread(target=lambda:
            subprocess.run(["python", "tests/test_latency.py"]), daemon=True
        ).start()

    # Stop All Services
    def stop_all(self):
        self.log(" Power Down - Complete Shutdown")
        self.status_led.itemconfig(self.led_circle, fill="#f85149")
        for name, proc in self.processes.items():
            try:
                p = psutil.Process(proc.pid)
                for child in p.children(recursive=True):
                    child.terminate()
                p.terminate()
                self.log(f" {name} Stopped")
            except: pass
        self.processes.clear()
        self.start_time = None

if __name__ == "__main__":
    root = tk.Tk()
    EnterpriseGatewayUI(root)
    root.mainloop()
