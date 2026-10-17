"""
Unit tests for SQLite Memory Module
"""
import unittest
from kirve.memory import KirveMemory

class TestKirveMemory(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database for isolation and fast execution
        self.memory = KirveMemory(db_path=":memory:")

    def tearDown(self):
        self.memory.close()

    def test_add_and_retrieve_message(self):
        msg_id = self.memory.add_message(
            role="user",
            content="Merhaba KİRVE",
            session_id="test_sess",
            metadata={"source": "cli"}
        )
        self.assertIsInstance(msg_id, int)
        
        history = self.memory.get_history(session_id="test_sess", limit=5)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "Merhaba KİRVE")
        self.assertEqual(history[0]["metadata"]["source"], "cli")

    def test_chronological_order(self):
        self.memory.add_message("user", "İlk soru", session_id="order_sess")
        self.memory.add_message("assistant", "İlk cevap", session_id="order_sess")
        self.memory.add_message("user", "İkinci soru", session_id="order_sess")

        history = self.memory.get_history(session_id="order_sess", limit=10)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["content"], "İlk soru")
        self.assertEqual(history[1]["content"], "İlk cevap")
        self.assertEqual(history[2]["content"], "İkinci soru")

    def test_preferences(self):
        # Test string preference
        self.memory.set_preference("dil", "tr")
        self.assertEqual(self.memory.get_preference("dil"), "tr")

        # Test structured preference (dict)
        settings = {"theme": "dark", "sound": False}
        self.memory.set_preference("ui_settings", settings)
        self.assertEqual(self.memory.get_preference("ui_settings"), settings)

        # Test default when missing
        self.assertEqual(self.memory.get_preference("non_existent", "default_val"), "default_val")

    def test_clear_history(self):
        self.memory.add_message("user", "S1", session_id="sess_a")
        self.memory.add_message("user", "S2", session_id="sess_b")

        # Clear only sess_a
        cleared_count = self.memory.clear_history(session_id="sess_a")
        self.assertEqual(cleared_count, 1)
        self.assertEqual(len(self.memory.get_history(session_id="sess_a")), 0)
        self.assertEqual(len(self.memory.get_history(session_id="sess_b")), 1)

        # Clear all
        self.memory.clear_history()
        self.assertEqual(len(self.memory.get_history(session_id="sess_b")), 0)

    def test_log_event(self):
        self.memory.log_event("INFO", "Sistem başlatıldı.")
        with self.memory._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM system_logs WHERE level = 'INFO'")
            rows = cursor.fetchall()
            self.assertEqual(len(rows), 1)

if __name__ == "__main__":
    unittest.main()
