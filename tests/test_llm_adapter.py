"""
Unit tests for Local LLM Adapter and Fallback Mechanism
"""
import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import io
import json
from kirve.llm_adapter import OllamaAdapter

class TestOllamaAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = OllamaAdapter(base_url="http://localhost:11434", default_model="test-model")

    @patch("urllib.request.urlopen")
    def test_check_health_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({"version": "0.1.32"}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        healthy, msg = self.adapter.check_health()
        self.assertTrue(healthy)
        self.assertIn("0.1.32", msg)

    @patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused"))
    def test_check_health_failure(self, mock_urlopen):
        healthy, msg = self.adapter.check_health()
        self.assertFalse(healthy)
        self.assertIn("Connection refused", msg)

    @patch("kirve.network.NetworkChecker.is_online", return_value=False)
    @patch.object(OllamaAdapter, "check_health", return_value=(False, "Connection refused"))
    def test_fallback_when_offline_and_ollama_down(self, mock_health, mock_net):
        """
        Verify the fallback mechanism when offline and local model service is down.
        """
        resp = self.adapter.generate_response(prompt="Test prompt")
        self.assertFalse(resp["success"])
        self.assertFalse(resp["is_online"])
        self.assertIn("çevrimdışıyız", resp["content"])
        self.assertIn("ollama run", resp["content"])
        self.assertIn("patron", resp["content"].lower())

    @patch("kirve.network.NetworkChecker.is_online", return_value=True)
    @patch.object(OllamaAdapter, "check_health", return_value=(False, "Connection refused"))
    def test_fallback_when_online_and_ollama_down(self, mock_health, mock_net):
        """
        Verify fallback when internet is online but local Ollama is not active.
        """
        resp = self.adapter.generate_response(prompt="Test prompt")
        self.assertFalse(resp["success"])
        self.assertTrue(resp["is_online"])
        self.assertIn("yerel Ollama servisi", resp["content"])
        self.assertIn("patron", resp["content"].lower())

    @patch("kirve.network.NetworkChecker.is_online", return_value=False)
    @patch.object(OllamaAdapter, "check_health", return_value=(True, "Ollama aktif"))
    @patch("urllib.request.urlopen")
    def test_successful_offline_local_generation(self, mock_urlopen, mock_health, mock_net):
        """
        Verify that if offline, but Ollama is running, local generation succeeds.
        """
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_data = {
            "model": "test-model",
            "message": {
                "role": "assistant",
                "content": "Emredersin patron, yerel modda görev tamam."
            }
        }
        mock_resp.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        resp = self.adapter.generate_response(
            prompt="Yerel durum nedir?",
            history=[{"role": "user", "content": "Selam"}]
        )
        self.assertTrue(resp["success"])
        self.assertFalse(resp["is_online"]) # Confirms it worked purely offline
        self.assertTrue(resp["is_local"])
        self.assertEqual(resp["content"], "Emredersin patron, yerel modda görev tamam.")

    @patch("kirve.network.NetworkChecker.is_online", return_value=True)
    @patch.object(OllamaAdapter, "check_health", return_value=(True, "Ollama aktif"))
    @patch("urllib.request.urlopen")
    def test_http_error_handling(self, mock_urlopen, mock_health, mock_net):
        """
        Verify handling when Ollama returns an HTTP error (e.g. 404 model not found).
        """
        mock_error = urllib.error.HTTPError(
            url="http://localhost:11434/api/chat",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(b'{"error": "model not found"}')
        )
        mock_urlopen.side_effect = mock_error

        resp = self.adapter.generate_response(prompt="Hello")
        self.assertFalse(resp["success"])
        self.assertIn("ollama pull", resp["content"])

if __name__ == "__main__":
    unittest.main()
