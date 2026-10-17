"""
Unit tests for Focus Monitor, Fullscreen Detection and Event Bus
"""
import unittest
from kirve.event_bus import EventBus
from kirve.focus_monitor import FocusMonitor

class TestFocusMonitor(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()
        self.monitor = FocusMonitor(event_bus=self.bus, poll_interval=0.1)

    def tearDown(self):
        self.monitor.stop_monitoring()

    def test_event_bus_pub_sub(self):
        received = []
        def handler(event):
            received.append(event.data)

        self.bus.subscribe("TEST_EVENT", handler)
        self.bus.publish("TEST_EVENT", {"status": "ok"})
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["status"], "ok")

    def test_fullscreen_enter_triggers_silent_mode(self):
        events_received = []
        self.bus.subscribe("FULLSCREEN_ENTER", lambda e: events_received.append("FS_ENTER"))
        self.bus.subscribe("SILENT_MODE_CHANGED", lambda e: events_received.append(f"SILENT_{e.data['silent_mode']}"))

        # Simulate entering fullscreen game
        mock_fullscreen = {
            "title": "Cyberpunk 2077 (Oyunda)",
            "rect": (0, 0, 1920, 1080),
            "is_fullscreen": True,
            "is_meeting_or_game": True,
            "should_be_silent": True
        }

        changed = self.monitor.check_and_update(mock_fullscreen)
        self.assertTrue(changed)
        self.assertTrue(self.monitor.silent_mode)
        self.assertIn("FS_ENTER", events_received)
        self.assertIn("SILENT_True", events_received)

    def test_fullscreen_exit_restores_normal_mode(self):
        events_received = []
        self.bus.subscribe("FULLSCREEN_EXIT", lambda e: events_received.append("FS_EXIT"))
        self.bus.subscribe("SILENT_MODE_CHANGED", lambda e: events_received.append(f"SILENT_{e.data['silent_mode']}"))

        # Put into fullscreen first
        self.monitor.check_and_update({
            "title": "Zoom Meeting",
            "rect": (0, 0, 1920, 1080),
            "is_fullscreen": True,
            "is_meeting_or_game": True,
            "should_be_silent": True
        })
        self.assertTrue(self.monitor.silent_mode)

        # Now simulate window back to normal desktop window
        mock_windowed = {
            "title": "Notepad",
            "rect": (100, 100, 800, 600),
            "is_fullscreen": False,
            "is_meeting_or_game": False,
            "should_be_silent": False
        }

        changed = self.monitor.check_and_update(mock_windowed)
        self.assertTrue(changed)
        self.assertFalse(self.monitor.silent_mode)
        self.assertIn("FS_EXIT", events_received)
        self.assertIn("SILENT_False", events_received)

    def test_screen_resolution_returns_valid_tuple(self):
        w, h = self.monitor.get_screen_resolution()
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)

if __name__ == "__main__":
    unittest.main()
