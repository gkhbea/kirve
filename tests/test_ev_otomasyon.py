"""
Unit tests for Ev Otomasyonu (Google Home, Togg T10X, Roborock Q8 and Resilient Retry Mechanism)
"""
import unittest
import time
from kirve.memory import KirveMemory
from kirve.tools.ev_otomasyon import EvOtomasyonAraci, ToggT10XStatus, RoborockQ8Status

class TestEvOtomasyon(unittest.TestCase):
    def setUp(self):
        self.memory = KirveMemory(db_path=":memory:")
        self.automation = EvOtomasyonAraci(memory=self.memory)

    def tearDown(self):
        self.automation.close()
        self.memory.close()

    def test_togg_status_normal(self):
        res = self.automation.get_togg_status()
        self.assertTrue(res["success"])
        telemetry = res["telemetry"]
        self.assertIn("battery_percentage", telemetry)
        self.assertIn("range_km", telemetry)
        self.assertGreaterEqual(telemetry["battery_percentage"], 0)
        self.assertLessEqual(telemetry["battery_percentage"], 100)

    def test_togg_charging_toggle(self):
        res = self.automation.set_togg_charging(start=True)
        self.assertTrue(res["success"])
        self.assertTrue(res["telemetry"]["is_charging"])
        self.assertGreater(res["telemetry"]["charging_power_kw"], 0)

        res_stop = self.automation.set_togg_charging(start=False)
        self.assertFalse(res_stop["telemetry"]["is_charging"])

    def test_roborock_status_normal(self):
        res = self.automation.get_roborock_status()
        self.assertTrue(res["success"])
        telemetry = res["telemetry"]
        self.assertIn("lidar_status", telemetry)
        self.assertEqual(telemetry["lidar_status"], "OK")

    def test_roborock_zone_cleaning(self):
        res = self.automation.start_zone_cleaning(zone_name="Salon")
        self.assertTrue(res["success"])
        self.assertEqual(res["telemetry"]["cleaning_state"], "cleaning")
        self.assertEqual(res["telemetry"]["current_zone"], "Salon")

        # Dock robot
        res_dock = self.automation.dock_roborock()
        self.assertTrue(res_dock["success"])
        self.assertEqual(res_dock["telemetry"]["cleaning_state"], "docked")

    def test_roborock_lidar_blocked_fails_gracefully(self):
        self.automation._roborock_status.lidar_status = "BLOCKED"
        res = self.automation.start_zone_cleaning(zone_name="Mutfak")
        self.assertFalse(res["success"])
        self.assertIn("LiDAR", res["error"])

    def test_google_home_controls(self):
        devices = self.automation.list_home_devices()
        self.assertGreaterEqual(len(devices), 3)

        # Control light
        cmd_res = self.automation.control_home_device("light_salon", "turn_off")
        self.assertTrue(cmd_res["success"])
        self.assertFalse(cmd_res["current_state"]["on"])

    def test_togg_timeout_resilience_and_retry(self):
        # Trigger simulated timeout
        self.automation.simulate_togg_timeout = True

        res = self.automation.get_togg_status()
        # Verify it did NOT crash, returned graceful status
        self.assertFalse(res["success"])
        self.assertTrue(res.get("is_timeout", False))
        self.assertIn("cached_telemetry", res)
        self.assertIn("retry_task_id", res)

        # Verify task was added to background retry queue
        queue_status = self.automation.get_retry_status()
        self.assertEqual(len(queue_status), 1)
        self.assertEqual(queue_status[0]["device_name"], "Togg T10X")

        # Verify log entry in SQLite memory
        history = self.memory.get_history(limit=5)
        with self.memory._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_logs WHERE level = 'WARNING'")
            logs = cursor.fetchall()
            self.assertGreaterEqual(len(logs), 1)
            self.assertIn("Togg T10X", logs[0]["message"])

    def test_roborock_timeout_resilience_and_recovery(self):
        # Trigger simulated timeout on Roborock
        self.automation.simulate_roborock_timeout = True
        res = self.automation.get_roborock_status()
        self.assertFalse(res["success"])
        self.assertTrue(res.get("is_timeout"))

        # Now simulate network recovery
        self.automation.simulate_roborock_timeout = False

        # Allow worker thread to run a cycle
        time.sleep(2.5)

        # Retry queue should have drained after successful retry
        queue_status = self.automation.get_retry_status()
        self.assertEqual(len(queue_status), 0)

    def test_togg_typed_requests(self):
        from kirve.tools.ev_otomasyon import ToggChargeRequest, ToggClimateRequest, ToggLockRequest
        
        # Test charge request
        charge_req = ToggChargeRequest(vin="TR-TOGG-01", action="START", target_soc_percentage=90)
        res_charge = self.automation.send_togg_charge_request(charge_req)
        self.assertTrue(res_charge.success)
        self.assertTrue(res_charge.telemetry["is_charging"])

        # Test climate request
        climate_req = ToggClimateRequest(vin="TR-TOGG-01", action="START", target_temperature_c=21.5)
        res_climate = self.automation.send_togg_climate_request(climate_req)
        self.assertTrue(res_climate.success)
        self.assertTrue(res_climate.telemetry["climate_active"])
        self.assertEqual(res_climate.telemetry["target_temperature_c"], 21.5)

        # Test lock request
        lock_req = ToggLockRequest(vin="TR-TOGG-01", lock=True)
        res_lock = self.automation.send_togg_lock_request(lock_req)
        self.assertTrue(res_lock.success)
        self.assertTrue(res_lock.telemetry["doors_locked"])

    def test_roborock_typed_request(self):
        from kirve.tools.ev_otomasyon import RoborockCleanRequest
        clean_req = RoborockCleanRequest(device_id="RR-01", command="clean_zone", zone_name="Mutfak", water_level="high")
        res = self.automation.send_roborock_clean_request(clean_req)
        self.assertTrue(res.success)
        self.assertEqual(res.telemetry["cleaning_state"], "cleaning")
        self.assertEqual(res.telemetry["current_zone"], "Mutfak")
        self.assertEqual(res.telemetry["water_level"], "high")

    def test_google_home_typed_command(self):
        from kirve.tools.ev_otomasyon import GoogleHomeCommandRequest
        req = GoogleHomeCommandRequest(device_id="light_salon", command="turn_on")
        res = self.automation.execute_google_home_command(req)
        self.assertTrue(res.success)
        self.assertTrue(res.current_state["on"])

if __name__ == "__main__":
    unittest.main()
