"""
Unit tests for Network Module
"""
import unittest
from unittest.mock import patch
import socket
from kirve.network import NetworkChecker

class TestNetworkChecker(unittest.TestCase):
    @patch("socket.create_connection")
    def test_is_online_true(self, mock_create):
        # Mock successful connection
        mock_create.return_value.__enter__.return_value = None
        self.assertTrue(NetworkChecker.is_online())
        status, desc = NetworkChecker.get_network_status()
        self.assertTrue(status)
        self.assertIn("Çevrimiçi", desc)

    @patch("socket.create_connection", side_effect=socket.timeout)
    def test_is_online_false_on_timeout(self, mock_create):
        self.assertFalse(NetworkChecker.is_online())
        status, desc = NetworkChecker.get_network_status()
        self.assertFalse(status)
        self.assertIn("Çevrimdışı", desc)

    @patch("socket.create_connection", side_effect=OSError("Network unreachable"))
    def test_is_online_false_on_os_error(self, mock_create):
        self.assertFalse(NetworkChecker.is_online())

if __name__ == "__main__":
    unittest.main()
