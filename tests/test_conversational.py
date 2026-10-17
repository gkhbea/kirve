"""
Unit tests for Thoughtful Conversational & Research Engine (JARVIS Style)
"""
import unittest
from unittest.mock import patch
from kirve.conversational import ConversationalEngine

class TestConversationalEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ConversationalEngine()

    def test_empty_input(self):
        reply = self.engine.get_commentary_and_reply("")
        self.assertTrue(len(reply) > 5)

    def test_greetings_thoughtful(self):
        reply = self.engine.get_commentary_and_reply("Nasılsın?")
        self.assertTrue(len(reply) > 15)
        self.assertTrue(any(w in reply.lower() for w in ["iyiyim", "noktadayız", "zindeyim", "çalışıyor", "hazırım"]))

    def test_opinion_hardware(self):
        reply = self.engine.get_commentary_and_reply("Sistem ve donanım hakkında ne düşünüyorsun?")
        self.assertTrue("işlemci" in reply.lower() or "ram" in reply.lower() or "donanım" in reply.lower())
        self.assertTrue("yüzde" in reply.lower() or "çalışıyor" in reply.lower())

    def test_opinion_togg(self):
        ctx = {"togg_soc": 85, "togg_range": 420, "togg_charging": False}
        reply = self.engine.get_commentary_and_reply("Togg sence nasıl?", device_context=ctx)
        self.assertIn("togg", reply.lower())
        self.assertTrue("menzil" in reply.lower() or "batarya" in reply.lower())

    def test_opinion_roborock(self):
        reply = self.engine.get_commentary_and_reply("Süpürge hakkında fikrin ne?")
        self.assertIn("roborock", reply.lower())

    def test_cheapest_nutella_and_open_browser(self):
        with patch("webbrowser.open", return_value=True) as mock_open:
            reply = self.engine.get_commentary_and_reply("1 kg luk nutella en ucuz nerede arastır")
            self.assertTrue("nutella" in reply.lower())
            self.assertTrue("akakçe" in reply.lower() or "uygun" in reply.lower() or "açıyorum" in reply.lower())
            mock_open.assert_called_once()
            args, _ = mock_open.call_args
            self.assertIn("akakce.com", args[0])
            self.assertIn("nutella", args[0])

    def test_research_web_trigger(self):
        fake_results = {
            "success": True,
            "results": [
                {"title": "Hava Durumu İstanbul", "snippet": "İstanbul genelinde hava parçalı bulutlu ve 21 derece."}
            ]
        }
        with patch.object(self.engine.research_agent, "search_web", return_value=fake_results):
            reply = self.engine.get_commentary_and_reply("İstanbul hava durumunu araştır bakalım")
            self.assertTrue(any(w in reply.lower() for w in ["araştırdım", "bulgulara", "kaynakları"]))
            self.assertTrue("bulutlu" in reply.lower() or "derece" in reply.lower())

    def test_speech_cleaning(self):
        cleaned = self.engine._clean_for_speech("### **Merhaba** _sistem_ `[test]`")
        self.assertEqual(cleaned, "Merhaba sistem test")

if __name__ == "__main__":
    unittest.main()
