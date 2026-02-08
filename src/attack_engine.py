import random
import time
from core.event_bus import EventBus

class AttackEngine:

    def __init__(self, event_bus: EventBus):
        self.bus = event_bus

    def dos_attack(self):

        for _ in range(200):
            self.bus.publish("attack.event", {
                "type":"DOS",
                "severity":"HIGH"
            })
            time.sleep(0.01)

    def bit_flip(self):

        self.bus.publish("attack.event",{
            "type":"BIT_FLIP"
        })

    def heartbeat_drop(self):

        self.bus.publish("attack.event",{
            "type":"HEARTBEAT_LOSS"
        })
