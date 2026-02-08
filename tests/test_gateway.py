import unittest
from src.master_gateway import GatewayEngine


class TestGatewayEngine(unittest.TestCase):

    def setUp(self):
        self.engine = GatewayEngine()

    def test_engine_init(self):
        self.assertIsNotNone(self.engine.bus)
        self.assertIsNotNone(self.engine.ble)
        self.assertIsNotNone(self.engine.can)
        self.assertEqual(self.engine.threads, [])

    def test_start(self):
        self.engine.start()
        self.assertTrue(len(self.engine.threads) > 0)

    def test_stop(self):
        self.engine.stop()
        self.assertFalse(self.engine.can.running)


if __name__ == "__main__":
    unittest.main()
