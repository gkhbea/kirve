"""
Unit tests for System Telemetry (psutil real hardware data)
"""
import unittest
from kirve.telemetry import SystemTelemetry

class TestSystemTelemetry(unittest.TestCase):
    def setUp(self):
        self.telemetry = SystemTelemetry()

    def test_snapshot_metrics(self):
        data = self.telemetry.get_snapshot()

        # CPU
        self.assertIn("cpu_percent", data)
        self.assertGreaterEqual(data["cpu_percent"], 0.0)
        self.assertLessEqual(data["cpu_percent"], 100.0)
        self.assertGreaterEqual(data["cpu_count"], 1)

        # RAM
        self.assertIn("ram_percent", data)
        self.assertGreater(data["ram_total_gb"], 0.0)
        self.assertGreater(data["ram_used_gb"], 0.0)
        self.assertLessEqual(data["ram_used_gb"], data["ram_total_gb"] + 0.5)

        # Network
        self.assertIn("net_download_kb_s", data)
        self.assertIn("net_upload_kb_s", data)
        self.assertGreaterEqual(data["net_download_kb_s"], 0.0)
        self.assertGreaterEqual(data["net_upload_kb_s"], 0.0)

if __name__ == "__main__":
    unittest.main()
