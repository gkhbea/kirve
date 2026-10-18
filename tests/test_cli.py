import unittest
from unittest.mock import patch, MagicMock
from kirve.cli import KirveCLI
from kirve.memory import KirveMemory

class TestKirveCLI(unittest.TestCase):
    def setUp(self):
        self.cli = KirveCLI(session_id="test_cli_sess")
        self.cli.memory = KirveMemory(db_path=":memory:")

    def tearDown(self):
        self.cli.focus_monitor.stop_monitoring()
        self.cli.research_agent.close()
        self.cli.memory.close()

    def test_handle_command_help(self):
        res = self.cli.handle_command("/yardim")
        self.assertTrue(res)

    def test_handle_command_status(self):
        res = self.cli.handle_command("/durum")
        self.assertTrue(res)

    def test_handle_command_history(self):
        self.cli.memory.add_message("user", "Test mesajı", session_id="test_cli_sess")
        res = self.cli.handle_command("/gecmis")
        self.assertTrue(res)

    def test_unknown_command(self):
        res = self.cli.handle_command("merhaba")
        self.assertFalse(res)

if __name__ == "__main__":
    unittest.main()
