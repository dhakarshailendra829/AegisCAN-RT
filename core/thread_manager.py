import threading
import time

class ThreadManager:
    def __init__(self):
        self.threads = {}
        self.lock = threading.Lock()

    def start_thread(self, name, target):

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()

        with self.lock:
            self.threads[name] = thread

    def health_status(self):

        status = {}

        with self.lock:
            for name, thread in self.threads.items():
                status[name] = thread.is_alive()

        return status
