import unittest
from core.event_bus import EventBus
from src.attack_engine import AttackEngine


class TestSecurity(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.attack = AttackEngine(self.bus)

    def test_attack_init(self):
        self.assertIsNotNone(self.attack)

    def test_bit_flip(self):
        self.attack.bit_flip()

    def test_heartbeat_drop(self):
        self.attack.heartbeat_drop()


if __name__ == "__main__":
    unittest.main()
