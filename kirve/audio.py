"""
KİRVE AI OS - Voice & Speech Module (STT & TTS)
- Speech-to-Text (STT) via faster-whisper
- Text-to-Speech (TTS) via pyttsx3 (Turkish SAPI5 voice support)
- Silent Mode & DND awareness
"""
import os
import sys
import time
import ctypes
import threading
import queue
from pathlib import Path
from typing import Optional, List, Callable

# faster-whisper STT
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# pyttsx3 TTS
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# edge-tts (Ultra-realistic Microsoft Neural Turkish voice)
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

class VoiceEngine:
    """
    Speech recognition and synthesis engine for KİRVE.
    Speaks in ultra-natural Turkish male voice (tr-TR-AhmetNeural via Edge-TTS)
    with deep, articulate baritone tone, backed by Windows OneCore Tolga & pyttsx3.
    Equipped with wake-word ('KİRVE') continuous background detection.
    """
    def __init__(self, whisper_model_size: str = "tiny", language: str = "tr"):
        self.language = language
        self.model_size = whisper_model_size
        self._whisper_model = None
        self.silent_mode = False
        self.is_speaking = False
        self.is_listening_to_command = False
        self._speech_queue = queue.Queue()
        self._worker_thread = None
        self._sapi_available = False
        self._pyttsx3_engine = None
        self._wake_word_running = False
        self._wake_word_thread = None

        # Start dedicated background TTS worker thread
        self._start_tts_worker()

    def _start_tts_worker(self):
        def _worker_loop():
            # Try initializing native Windows SAPI with Microsoft Tolga (OneCore Turkish Male)
            sapi_voice = None
            if sys.platform == "win32":
                try:
                    import pythoncom
                    import win32com.client
                    pythoncom.CoInitialize()
                    sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
                    cat = win32com.client.Dispatch("SAPI.SpObjectTokenCategory")
                    
                    # Search for Turkish male voice in OneCore tokens
                    token_found = False
                    for hive in [
                        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices",
                        r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices"
                    ]:
                        try:
                            cat.SetId(hive, False)
                            for t in cat.EnumerateTokens():
                                desc = t.GetDescription().lower()
                                if "tolga" in desc or ("turkish" in desc and "female" not in desc):
                                    sapi_voice.Voice = t
                                    token_found = True
                                    break
                        except Exception:
                            continue
                        if token_found:
                            break
                    
                    # -1 or -2 gives deliberate, clear ("tane tane"), deep ("tok") speech
                    sapi_voice.Rate = -1
                    sapi_voice.Volume = 100
                    self._sapi_available = True
                except Exception:
                    sapi_voice = None

            # Fallback to pyttsx3 if SAPI COM initialization failed
            pyttsx3_eng = None
            if not sapi_voice and PYTTSX3_AVAILABLE:
                try:
                    pyttsx3_eng = pyttsx3.init()
                    pyttsx3_eng.setProperty("rate", 140)
                    pyttsx3_eng.setProperty("volume", 1.0)
                    for v in pyttsx3_eng.getProperty("voices"):
                        v_name = v.name.lower()
                        if "tolga" in v_name or "turkish" in v_name:
                            pyttsx3_eng.setProperty("voice", v.id)
                            break
                except Exception:
                    pyttsx3_eng = None

            # Process speech queue
            while True:
                item = self._speech_queue.get()
                if item is None:
                    break
                text, on_finished = item
                if not self.silent_mode and text:
                    spoken_text = text.strip()
                    self.is_speaking = True
                    try:
                        # 1. Try ultra-realistic neural Turkish male voice (tr-TR-AhmetNeural via Edge-TTS)
                        played = self._speak_neural(spoken_text)

                        # 2. Local fallback if neural TTS is unavailable or offline
                        if not played:
                            if sapi_voice:
                                try:
                                    sapi_voice.Speak(spoken_text, 0)
                                except Exception:
                                    pass
                            elif pyttsx3_eng:
                                try:
                                    pyttsx3_eng.say(spoken_text)
                                    pyttsx3_eng.runAndWait()
                                except Exception:
                                    pass
                    finally:
                        self.is_speaking = False

                if on_finished:
                    try:
                        on_finished()
                    except Exception:
                        pass
                self._speech_queue.task_done()

            if sys.platform == "win32":
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

        self._worker_thread = threading.Thread(target=_worker_loop, daemon=True, name="KirveTTSWorker")
        self._worker_thread.start()

    def _speak_neural(self, text: str) -> bool:
        """
        Synthesizes high-fidelity, ultra-realistic Turkish male voice
        (tr-TR-AhmetNeural) via Edge-TTS and plays it with zero distortion via Windows MCI.
        """
        if not EDGE_TTS_AVAILABLE:
            return False

        import asyncio
        import hashlib
        cache_dir = Path.home() / ".kirve_tmp" / "tts_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        h = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
        mp3_path = str(cache_dir / f"speech_{h}.mp3")

        try:
            if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) < 100:
                async def _gen():
                    comm = edge_tts.Communicate(
                        text=text,
                        voice="tr-TR-AhmetNeural",
                        rate="+0%",
                        pitch="+0Hz"
                    )
                    await comm.save(mp3_path)
                asyncio.run(_gen())

            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 100:
                if sys.platform == "win32":
                    winmm = ctypes.windll.winmm
                    abs_p = os.path.abspath(mp3_path)
                    alias = f"kv_{int(time.time() * 1000) % 100000}"
                    winmm.mciSendStringW(f'close {alias}', None, 0, None)
                    r1 = winmm.mciSendStringW(f'open "{abs_p}" type mpegvideo alias {alias}', None, 0, None)
                    if r1 == 0:
                        winmm.mciSendStringW(f'play {alias} wait', None, 0, None)
                        winmm.mciSendStringW(f'close {alias}', None, 0, None)
                        return True
        except Exception:
            try:
                if os.path.exists(mp3_path) and os.path.getsize(mp3_path) < 100:
                    os.remove(mp3_path)
            except Exception:
                pass
            return False
        return False

    @staticmethod
    def check_wake_word(text: str):
        """
        Checks if given speech contains the wake word 'kirve'.
        Returns (True, remaining_command_text) if found, otherwise (False, '').
        """
        if not text:
            return False, ""
        import re
        t = text.replace("İ", "i").replace("I", "ı").lower()
        m = re.search(r"\b(?:hey\s+)?(kirve[a-z]*|kırve[a-z]*)\b", t)
        if m:
            remaining = text[m.end():].strip()
            remaining = re.sub(r"^[,\.\-!\?\s]*(lütfen|bana|ve)?\s*", "", remaining, flags=re.IGNORECASE).strip()
            return True, remaining
        return False, ""

    def start_wake_word_listener(self, on_wake_word_detected: Callable[[str], None]):
        """
        Starts a continuous background listener for the wake word 'kirve'.
        When heard, immediately triggers on_wake_word_detected(command_text).
        """
        if self._wake_word_running:
            return
        self._wake_word_running = True

        def _wake_worker():
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                recognizer.energy_threshold = 300
                recognizer.dynamic_energy_threshold = True
                recognizer.pause_threshold = 0.5

                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    while self._wake_word_running:
                        if self.is_speaking or self.silent_mode or self.is_listening_to_command:
                            time.sleep(0.3)
                            continue

                        try:
                            audio = recognizer.listen(source, timeout=2.5, phrase_time_limit=3.5)
                            text = recognizer.recognize_google(audio, language="tr-TR")
                            if text:
                                is_wake, cmd = self.check_wake_word(text)
                                if is_wake:
                                    on_wake_word_detected(cmd)
                        except (sr.WaitTimeoutError, sr.UnknownValueError):
                            continue
                        except Exception:
                            time.sleep(0.5)
            except Exception:
                pass

        self._wake_word_thread = threading.Thread(target=_wake_worker, daemon=True, name="KirveWakeWordListener")
        self._wake_word_thread.start()

    def stop_wake_word_listener(self):
        """Stops the wake word listener loop."""
        self._wake_word_running = False

    def _get_whisper_model(self):
        """Lazy loads the faster-whisper model."""
        if not WHISPER_AVAILABLE:
            return None
        if self._whisper_model is None:
            try:
                # CPU device with INT8 quantization for fast and low memory usage
                self._whisper_model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8"
                )
            except Exception:
                self._whisper_model = None
        return self._whisper_model

    def speak(self, text: str, blocking: bool = False, on_finished: Optional[Callable[[], None]] = None) -> bool:
        """
        Synthesizes speech in Turkish male voice (Tolga) with deep, articulate tone.
        Respects silent_mode (DND): if active, will NOT speak out loud.
        Calls on_finished() callback when speaking concludes.
        """
        if self.silent_mode:
            if on_finished:
                on_finished()
            return False

        if blocking:
            done_evt = threading.Event()
            def _done():
                done_evt.set()
                if on_finished:
                    on_finished()
            self._speech_queue.put((text, _done))
            done_evt.wait()
        else:
            self._speech_queue.put((text, on_finished))
        return True

    def transcribe_audio_file(self, audio_path: str) -> str:
        """
        Transcribes given audio file path.
        Uses SpeechRecognition (Google Turkish STT) first, then falls back to faster-whisper.
        """
        # 1. Try SpeechRecognition
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = r.record(source)
            text = r.recognize_google(audio, language="tr-TR")
            if text and text.strip():
                return text.strip()
        except Exception:
            pass

        # 2. Try faster-whisper if available
        model = self._get_whisper_model()
        if model:
            try:
                segments, info = model.transcribe(
                    audio_path,
                    language=self.language,
                    beam_size=3
                )
                text = " ".join(seg.text for seg in segments).strip()
                if text:
                    return text
            except Exception:
                pass

        return ""

    def simulate_voice_command(self, sample_text: str) -> str:
        """Helper for test suites and simulated microphone input."""
        return sample_text.strip()

    def record_microphone_wav(self, output_path: str, duration_seconds: float = 3.0) -> bool:
        """
        Records microphone audio into a standard 16-bit 16kHz mono PCM WAV file.
        Uses PyAudio if available; falls back to Windows MCI.
        """
        # Try PyAudio first
        try:
            import pyaudio
            import wave
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000

            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            frames = []
            num_frames = int(RATE / CHUNK * duration_seconds)
            for _ in range(num_frames):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            stream.stop_stream()
            stream.close()
            p.terminate()

            with wave.open(output_path, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b"".join(frames))

            p_out = Path(output_path)
            if p_out.exists() and p_out.stat().st_size > 100:
                return True
        except Exception:
            pass

        # Fallback to Windows winmm.dll MCI
        if sys.platform == "win32":
            try:
                winmm = ctypes.windll.winmm
                winmm.mciSendStringW("close recsound", None, 0, None)
                winmm.mciSendStringW("open new type waveaudio alias recsound", None, 0, None)
                winmm.mciSendStringW("record recsound", None, 0, None)
                time.sleep(duration_seconds)
                winmm.mciSendStringW("stop recsound", None, 0, None)
                winmm.mciSendStringW(f'save recsound "{output_path}"', None, 0, None)
                winmm.mciSendStringW("close recsound", None, 0, None)
                p = Path(output_path)
                return p.exists() and p.stat().st_size > 44
            except Exception:
                pass

        return False

    def listen_and_transcribe(self, duration_seconds: float = 3.5) -> str:
        """
        Listens to microphone speech and transcribes it into Turkish text.
        Employs native Voice Activity Detection (VAD) via SpeechRecognition.
        Gracefully returns empty string if no speech was detected.
        """
        # 1. Direct SpeechRecognition with native PyAudio Microphone
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            r.energy_threshold = 300
            r.dynamic_energy_threshold = True
            with sr.Microphone() as source:
                # Listen up to duration_seconds
                audio = r.listen(source, timeout=3.0, phrase_time_limit=duration_seconds)
            text = r.recognize_google(audio, language="tr-TR")
            if text and text.strip():
                return text.strip()
        except Exception:
            pass

        # 2. File-based fallback recording & transcription
        import tempfile
        tmp_dir = Path.home() / ".kirve_tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = str(tmp_dir / f"rec_{int(time.time() * 1000)}.wav")
        try:
            ok = self.record_microphone_wav(tmp_path, duration_seconds=duration_seconds)
            if ok:
                return self.transcribe_audio_file(tmp_path)
            return ""
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass

# Module-level convenience alias
check_wake_word = VoiceEngine.check_wake_word

