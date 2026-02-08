import threading
import os
import csv
from core.event_bus import EventBus
from core.logger_engine import LoggerEngine
from src.ble_receiver import BLEReceiver
from src.can_translator import CANTranslator
from src.attack_engine import AttackEngine


class GatewayEngine:

    def __init__(self):

        self.bus = EventBus()
        self.logger = LoggerEngine()

        self.ble = BLEReceiver(self.bus)
        self.can = CANTranslator(self.bus)
        self.attack = AttackEngine(self.bus)

        self.threads = []
        self.running = False
        self.telemetry = []

        os.makedirs("data", exist_ok=True)

        # subscribe to CAN telemetry
        self.bus.subscribe("can.tx", self._on_can_tx)
        self.bus.subscribe("attack.event", self._on_attack)
    def _on_can_tx(self, data):

        data["type"] = "CAN"
        self.telemetry.append(data)

        if len(self.telemetry) > 300:
            self.telemetry.pop(0)


    def _on_attack(self, data):

        data["type"] = "ATTACK"
        self.telemetry.append(data)

    def handle_can_tx(self, data):

        self.telemetry.append(data)

        if len(self.telemetry) > 500:
            self.telemetry.pop(0)

        # append CSV
        with open("data/telemetry_log.csv", "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["angle","latency","queue"])
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(data)

    def start(self):

        if self.running:
            return

        self.running = True

        self.threads = [
            threading.Thread(target=self.ble.start, daemon=True),
            threading.Thread(target=self.can.run, daemon=True),
        ]

        for t in self.threads:
            t.start()

        self.logger.info("Gateway Started")

    def stop(self):

        self.running = False
        self.ble.stop()
        self.can.stop()
        self.logger.info("Gateway Stopped")

    def run_attack(self, name):
        self.can.attack_mode = name
        if name == "dos":
            threading.Thread(target=self.attack.dos_attack, daemon=True).start()

        elif name == "flip":
            threading.Thread(target=self.attack.bit_flip, daemon=True).start()

        elif name == "heart":
            threading.Thread(target=self.attack.heartbeat_drop, daemon=True).start()
