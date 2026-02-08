import unittest
from src.can_translator import CANTranslator
from core.event_bus import EventBus


class TestPipeline(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus()
        self.translator = CANTranslator(self.bus)

    def test_scale_steering(self):
        result = self.translator.scale_steering(127)
        self.assertEqual(result, 0)

    def test_scale_range(self):
        low = self.translator.scale_steering(0)
        high = self.translator.scale_steering(255)

        self.assertTrue(low < 0)
        self.assertTrue(high > 0)


if __name__ == "__main__":
    unittest.main()
