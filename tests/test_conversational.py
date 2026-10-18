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

    def test_opinion_ai_future(self):
        reply = self.engine.get_commentary_and_reply("Yapay zeka hakkında ne düşünüyorsun?")
        self.assertTrue("yapay zeka" in reply.lower() or "modelin" in reply.lower())

    def test_capabilities_response(self):
        reply = self.engine.get_commentary_and_reply("Neler yapabilirsin?")
        self.assertTrue("araştırma" in reply.lower() or "donanım" in reply.lower())

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
        with patch.object(self.engine.research_agent, "open_in_foreground_browser", return_value=True):
            with patch.object(self.engine.research_agent, "search_web", return_value=fake_results):
                reply = self.engine.get_commentary_and_reply("İstanbul hava durumunu araştır bakalım")
                self.assertTrue(any(w in reply.lower() for w in ["araştırdım", "bulgulara", "kaynakları"]))
                self.assertTrue("bulutlu" in reply.lower() or "derece" in reply.lower())

    def test_directive_google_search_rule(self):
        reply = self.engine.get_commentary_and_reply("sana soru sordugumda google arastır")
        self.assertTrue("google" in reply.lower())
        self.assertTrue("soru" in reply.lower())
        self.assertTrue("anlaşıldı" in reply.lower() or "araştırma" in reply.lower())

    def test_question_triggers_google_search_and_browser(self):
        fake_results = {
            "success": True,
            "results": [
                {"title": "Galatasaray Maç Takvimi", "snippet": "Galatasaray maçı Pazar günü saat 19:00'da oynanacak."}
            ]
        }
        with patch.object(self.engine.research_agent, "open_in_foreground_browser", return_value=True) as mock_open:
            with patch.object(self.engine.research_agent, "search_web", return_value=fake_results):
                reply = self.engine.get_commentary_and_reply("Galatasaray maçı ne zaman?")
                mock_open.assert_called_once()
                args, _ = mock_open.call_args
                self.assertIn("google.com/search?q=", args[0])
                self.assertIn("Galatasaray", args[0])
                self.assertTrue("google" in reply.lower() or "araştırdım" in reply.lower())
                self.assertTrue("pazar" in reply.lower() or "oynanacak" in reply.lower() or "açtım" in reply.lower())

    def test_interrogative_without_question_mark_triggers_google(self):
        fake_results = {
            "success": True,
            "results": [
                {"title": "Python Programlama", "snippet": "Python yüksek seviyeli, genel amaçlı bir programlama dilidir."}
            ]
        }
        with patch.object(self.engine.research_agent, "open_in_foreground_browser", return_value=True) as mock_open:
            with patch.object(self.engine.research_agent, "search_web", return_value=fake_results):
                reply = self.engine.get_commentary_and_reply("Python nedir")
                mock_open.assert_called_once()
                args, _ = mock_open.call_args
                self.assertIn("google.com/search?q=", args[0])
                self.assertIn("Python", args[0])
                self.assertTrue("google" in reply.lower() or "araştırdım" in reply.lower() or "python" in reply.lower())

    def test_speech_cleaning(self):
        cleaned = self.engine._clean_for_speech("### **Merhaba** _sistem_ `[test]`")
        self.assertEqual(cleaned, "Merhaba sistem test")

if __name__ == "__main__":
    unittest.main()
