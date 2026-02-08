import psutil
import time
import threading

class MetricsEngine:

    def __init__(self,event_bus):

        self.bus = event_bus
        self.running = True

    def collect(self):

        while self.running:

            stats = {
                "cpu": psutil.cpu_percent(),
                "ram": psutil.virtual_memory().percent,
                "threads": threading.active_count(),
                "time": time.time()
            }

            self.bus.publish("system.metrics", stats)

            time.sleep(1)

    def start(self):
        threading.Thread(target=self.collect, daemon=True).start()

    def stop(self):
        self.running=False
