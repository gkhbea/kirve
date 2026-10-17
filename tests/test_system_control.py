"""
Unit tests for System Control Tool
"""
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from kirve.tools.system_control import SystemControlTool
from kirve.tools.security import SecurityAgent

class TestSystemControlTool(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_write_and_read_file(self):
        tool = SystemControlTool()
        test_file = self.temp_path / "test.txt"
        
        # Write
        write_res = tool.write_file(str(test_file), "KİRVE test içeriği")
        self.assertTrue(write_res["success"])
        self.assertTrue(test_file.exists())

        # Read
        read_res = tool.read_file(str(test_file))
        self.assertTrue(read_res["success"])
        self.assertEqual(read_res["content"], "KİRVE test içeriği")

    def test_delete_file_rejected_by_patron(self):
        # Security agent rejects deletion ('H')
        sec_agent = SecurityAgent(input_provider=lambda p: "h")
        tool = SystemControlTool(security_agent=sec_agent)

        target = self.temp_path / "protected.txt"
        target.write_text("Önemli veri", encoding="utf-8")

        res = tool.delete_file(str(target))
        self.assertFalse(res["success"])
        self.assertTrue(res.get("aborted", False))
        self.assertTrue(target.exists())  # File was NOT deleted

    def test_delete_file_approved_by_patron(self):
        # Security agent approves deletion ('E')
        sec_agent = SecurityAgent(input_provider=lambda p: "e")
        tool = SystemControlTool(security_agent=sec_agent)

        target = self.temp_path / "to_delete.txt"
        target.write_text("Silinecek veri", encoding="utf-8")

        res = tool.delete_file(str(target))
        self.assertTrue(res["success"])
        self.assertTrue(res.get("deleted", False))
        self.assertFalse(target.exists())  # File was deleted

    @patch("subprocess.Popen")
    def test_open_application(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_popen.return_value = mock_proc

        tool = SystemControlTool()
        res = tool.open_application("notepad.exe")

        self.assertTrue(res["success"])
        self.assertEqual(res["pid"], 1234)
        mock_popen.assert_called_once()

    def test_list_directory(self):
        (self.temp_path / "file1.txt").write_text("a")
        (self.temp_path / "subfolder").mkdir()

        tool = SystemControlTool()
        res = tool.list_directory(str(self.temp_path))

        self.assertTrue(res["success"])
        self.assertEqual(res["total_items"], 2)

if __name__ == "__main__":
    unittest.main()
