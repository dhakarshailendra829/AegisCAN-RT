# src/master_gateway.py - ENTERPRISE GRADE CONTROL PANEL
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import subprocess
import time
import queue
import os

class EnterpriseGatewayUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🏭 BLE-CAN Production Gateway Control Center")
        self.root.geometry("900x700")
        self.root.configure(bg="#0d1117")
        
        self.processes = {}
        self.log_queue = queue.Queue()
        
        self.setup_enterprise_ui()
        threading.Thread(target=self.log_display_loop, daemon=True).start()
    
    def setup_enterprise_ui(self):
        # Title Bar
        title_frame = tk.Frame(self.root, bg="#161b22", height=80)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="🚗 BLE-to-CAN Automotive Gateway", 
                font=("Consolas", 20, "bold"), fg="#58a6ff", bg="#161b22").pack(pady=15)
        
        # Control Panel
        control_frame = tk.Frame(self.root, bg="#0d1117")
        control_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Button(control_frame, text="🚀 START PRODUCTION", command=self.start_production,
                 bg="#238636", fg="white", font=("Consolas", 14, "bold"), 
                 width=18, height=2).pack(side="left", padx=10)
        
        tk.Button(control_frame, text="🧪 RUN TESTS", command=self.run_tests,
                 bg="#dbab09", fg="white", font=("Consolas", 14, "bold"), 
                 width=15, height=2).pack(side="left", padx=10)
        
        tk.Button(control_frame, text="🛑 EMERGENCY STOP", command=self.stop_all,
                 bg="#da3633", fg="white", font=("Consolas", 14, "bold"), 
                 width=18, height=2).pack(side="right", padx=10)
        
        self.status_label = tk.Label(control_frame, text="⏹️ OFFLINE", 
                                   fg="#f85149", font=("Consolas", 16, "bold"),
                                   bg="#0d1117")
        self.status_label.pack(side="right", padx=20)
        
        # Metrics Dashboard
        metrics_frame = tk.Frame(self.root, bg="#161b22")
        metrics_frame.pack(fill="x", padx=15, pady=5)
        
        self.latency_var = tk.StringVar(value="Latency: --")
        self.uptime_var = tk.StringVar(value="Uptime: 00:00")
        tk.Label(metrics_frame, textvariable=self.latency_var, fg="#ffaa00", 
                font=("Consolas", 12), bg="#161b22").pack(side="left", padx=20)
        tk.Label(metrics_frame, textvariable=self.uptime_var, fg="#66ccff", 
                font=("Consolas", 12), bg="#161b22").pack(side="right", padx=20)
        
        # Real-time Logs
        log_frame = tk.Frame(self.root, bg="#0d1117")
        log_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, bg="#161b22",
                                                 fg="#c9d1d9", font=("Consolas", 10),
                                                 state="disabled")
        self.log_text.pack(fill="both", expand=True)
    
    def log(self, message):
        self.log_queue.put(f"[{time.strftime('%H:%M:%S')}] {message}\n")
    
    def log_display_loop(self):
        while True:
            try:
                msg = self.log_queue.get(timeout=0.1)
                self.log_text.config(state="normal")
                self.log_text.insert(tk.END, msg)
                self.log_text.see(tk.END)
                self.log_text.config(state="disabled")
            except:
                pass
    
    def start_production(self):
        self.log("🎯 LAUNCHING PRODUCTION GATEWAY STACK...")
        threading.Thread(target=self._start_services, daemon=True).start()
    
    def _start_services(self):
        time.sleep(0.5)
        self.start_service("BLE_SIM", ["python", "src/ble_receiver.py"])
        time.sleep(1)
        self.start_service("CAN_GW", ["python", "src/can_translator.py"])
        time.sleep(1)
        self.start_service("HMI", ["python", "src/dashboard_gui.py"])
        self.status_label.config(text="✅ PRODUCTION ACTIVE", fg="#238636")
    
    def start_service(self, name, cmd):
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                  stderr=subprocess.STDOUT, text=True, 
                                  cwd=".", creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.processes[name] = proc
            self.log(f"✅ {name} started (PID: {proc.pid})")
        except Exception as e:
            self.log(f"❌ {name} FAILED: {e}")
    
    def run_tests(self):
        self.log("🧪 EXECUTING AUTOMOTIVE VALIDATION SUITE...")
        threading.Thread(target=lambda: subprocess.run(["python", "tests/test_latency.py"], 
                                                      cwd="."), daemon=True).start()
    
    def stop_all(self):
        self.log("🛑 EMERGENCY SHUTDOWN...")
        for name, proc in list(self.processes.items()):
            try:
                proc.terminate()
                self.log(f"🛑 {name} terminated")
            except:
                pass
        self.processes.clear()
        self.status_label.config(text="⏹️ OFFLINE", fg="#f85149")
    
    def read_output(self, name, proc):
        for line in iter(proc.stdout.readline, ''):
            self.log(f"{name}: {line.strip()}")

if __name__ == "__main__":
    root = tk.Tk()
    app = EnterpriseGatewayUI(root)
    root.mainloop()
