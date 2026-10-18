"""
Unit tests for Audio, STT and TTS Module
"""
import unittest
from unittest.mock import patch, MagicMock
from kirve.audio import VoiceEngine

class TestVoiceEngine(unittest.TestCase):
    def setUp(self):
        self.engine = VoiceEngine()

    def test_speak_respects_silent_mode(self):
        self.engine.silent_mode = True
        # In silent mode, speak() must return False and not produce sound
        res = self.engine.speak("Bu ses duyulmamalıdır.")
        self.assertFalse(res)

    def test_speak_normal_mode(self):
        self.engine.silent_mode = False
        # When not in silent mode, triggers speech synthesis
        res = self.engine.speak("Merhaba patron, sistem aktif.")
        self.assertTrue(res)

    def test_simulate_voice_command(self):
        cmd = self.engine.simulate_voice_command("Sistem durumunu göster")
        self.assertEqual(cmd, "Sistem durumunu göster")

    def test_listen_and_transcribe_mock(self):
        with patch.object(self.engine, "record_microphone_wav", return_value=True), \
             patch.object(self.engine, "transcribe_audio_file", return_value="En ucuz nutellayı bul"):
            text = self.engine.listen_and_transcribe(duration_seconds=0.1)
            self.assertEqual(text, "En ucuz nutellayı bul")

    def test_transcribe_missing_model_graceful_error(self):
        with patch.object(self.engine, "_get_whisper_model", return_value=None):
            res = self.engine.transcribe_audio_file("dummy.wav")
            self.assertEqual(res, "")

    def test_check_wake_word_detection(self):
        is_wake, cmd = self.engine.check_wake_word("kirve")
        self.assertTrue(is_wake)
        self.assertEqual(cmd, "")

        is_wake, cmd = self.engine.check_wake_word("Kirve 1 kg nutella nerede ucuz")
        self.assertTrue(is_wake)
        self.assertEqual(cmd, "1 kg nutella nerede ucuz")

        is_wake, cmd = self.engine.check_wake_word("hey kirvem hava durumu nasıl")
        self.assertTrue(is_wake)
        self.assertEqual(cmd, "hava durumu nasıl")

        is_wake, cmd = self.engine.check_wake_word("günaydın nasılsın")
        self.assertFalse(is_wake)

if __name__ == "__main__":
    unittest.main()
