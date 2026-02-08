import threading
from collections import defaultdict

class EventBus:
    def __init__(self):
        self.listeners = defaultdict(list)
        self.lock = threading.Lock()

    def subscribe(self, topic, callback):

        with self.lock:
            self.listeners[topic].append(callback)

    def publish(self, topic, data):

        callbacks = []

        with self.lock:
            callbacks = list(self.listeners.get(topic, []))

        for cb in callbacks:
            try:
                cb(data)
            except Exception as e:
                print(f"[EVENT BUS ERROR] {e}")
