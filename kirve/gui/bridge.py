"""
KİRVE AI OS - PySide6 QML Bridge
Connects real psutil telemetry, voice engine, and KİRVE tools to QML HUD.
"""
import sys
from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer
from kirve.telemetry import SystemTelemetry
from kirve.audio import VoiceEngine
from kirve.focus_monitor import FocusMonitor
from kirve.conversational import ConversationalEngine

class KirveHUDBridge(QObject):
    """
    Bridge communicating real-time data from Python to QML.
    """
    telemetryUpdated = Signal()
    messageReceived = Signal(str)
    voiceStateChanged = Signal(bool)
    startListeningRequested = Signal()
    statusIndicatorChanged = Signal()
    wakeWordTriggered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.telemetry = SystemTelemetry()
        self.voice = VoiceEngine()
        self.focus = FocusMonitor()
        self.conversational = ConversationalEngine()

        # Telemetry State Variables
        self._cpu_percent = 0.0
        self._ram_percent = 0.0
        self._ram_used_gb = 0.0
        self._ram_total_gb = 0.0
        self._net_down = "0.0 KB/s"
        self._net_up = "0.0 KB/s"

        # Assistant States
        self._silent_mode = False
        self._last_message = self.conversational.get_time_based_startup_greeting()
        self._status_indicator = "SİSTEM ÇEVRİMİÇİ ('KİRVE' DE DİNLEYEYİM)"
        self._is_listening = False

        # Connect thread-safe voice listening request signal
        self.startListeningRequested.connect(self.triggerVoiceInput)
        self.wakeWordTriggered.connect(self._on_wake_word_ui_slot)

        # Start continuous background listener for wake-word "KİRVE"
        self.voice.start_wake_word_listener(lambda cmd: self.wakeWordTriggered.emit(cmd))

        # Periodic timer for real-time 1Hz psutil telemetry updates
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_stats)
        self._timer.start(1000)

        # Initial sample
        self._refresh_stats()

        # Automatic hands-free greeting and microphone launch upon startup
        QTimer.singleShot(900, self._auto_greet_and_listen)

    def _auto_greet_and_listen(self):
        """Speaks the time-aware opening greeting to patron and immediately engages hands-free microphone listening."""
        greeting = self.conversational.get_time_based_startup_greeting()
        self._last_message = greeting
        self.messageReceived.emit(greeting)
        self.voice.speak(greeting, on_finished=self._on_speech_finished)

    def _on_speech_finished(self):
        """Invoked safely when speech finishes to trigger microphone without manual clicks."""
        self.startListeningRequested.emit()

    def _refresh_stats(self):
        stats = self.telemetry.get_snapshot()
        self._cpu_percent = stats["cpu_percent"]
        self._ram_percent = stats["ram_percent"]
        self._ram_used_gb = stats["ram_used_gb"]
        self._ram_total_gb = stats["ram_total_gb"]
        self._net_down = f"{stats['net_download_kb_s']} KB/s"
        self._net_up = f"{stats['net_upload_kb_s']} KB/s"
        self._silent_mode = self.focus.silent_mode
        self.telemetryUpdated.emit()

    # --- QML PROPERTIES ---

    @Property(float, notify=telemetryUpdated)
    def cpuPercent(self):
        return self._cpu_percent

    @Property(float, notify=telemetryUpdated)
    def ramPercent(self):
        return self._ram_percent

    @Property(float, notify=telemetryUpdated)
    def ramUsed(self):
        return self._ram_used_gb

    @Property(float, notify=telemetryUpdated)
    def ramTotal(self):
        return self._ram_total_gb

    @Property(str, notify=telemetryUpdated)
    def netDown(self):
        return self._net_down

    @Property(str, notify=telemetryUpdated)
    def netUp(self):
        return self._net_up

    @Property(bool, notify=telemetryUpdated)
    def silentMode(self):
        return self._silent_mode

    @Property(str, notify=messageReceived)
    def lastMessage(self):
        return self._last_message

    @Property(bool, notify=voiceStateChanged)
    def isListening(self):
        return self._is_listening

    @Property(str, notify=statusIndicatorChanged)
    def statusIndicator(self):
        return self._status_indicator

    # --- QML SLOTS ---

    @Slot(str)
    def sendCommand(self, cmd_text: str):
        c = cmd_text.strip().lower()
        if not c:
            return

        if any(w in c for w in ["ucuz", "fiyat", "nerede", "araştır", "arastir", "google", "web"]):
            self._status_indicator = "WEB SAYFASI AÇILIYOR..."
            self.statusIndicatorChanged.emit()

        if c in ["/togg", "togg", "togg şarj"]:
            reply = f"Togg T10X bataryası yüzde {self._togg_soc}, kalan menzil {self._togg_range} kilometre. Şarj durumu {'aktif' if self._togg_charging else 'kapalı'}."
        elif c in ["/roborock", "roborock", "süpürge"]:
            reply = f"Roborock Q8 LiDAR durumu {self._roborock_lidar}. İstasyonunda hazır bekliyor."
        elif "temizle" in c:
            self.automation.start_zone_cleaning("Salon")
            reply = "Roborock Q8 salonda LiDAR eşliğinde temizliğe başladı."
        elif "şarj" in c:
            self._togg_charging = not self._togg_charging
            state = "başlatıldı" if self._togg_charging else "durduruldu"
            reply = f"Togg T10X şarjı {state}."
        elif "ode" in c or "/ode" in c:
            reply = "Güvenlik protokolü: 18 bin 499 TL tutarındaki sepet ödemesini onaylıyor musun?"
        else:
            device_ctx = {
                "togg_soc": self._togg_soc,
                "togg_range": self._togg_range,
                "togg_charging": self._togg_charging,
                "roborock_lidar": self._roborock_lidar,
            }
            reply = self.conversational.get_commentary_and_reply(
                user_text=cmd_text,
                device_context=device_ctx
            )

        self._last_message = reply
        self.messageReceived.emit(reply)
        self._status_indicator = "SİSTEM ÇEVRİMİÇİ ('KİRVE' DE DİNLEYEYİM)"
        self.statusIndicatorChanged.emit()

        # Synthesize voice output if not in silent mode and chain hands-free listening
        self.voice.speak(reply, on_finished=self._on_speech_finished)

    @Slot(str)
    def _on_wake_word_ui_slot(self, cmd_text: str):
        """Triggered on Qt GUI main thread the instant 'KİRVE' is spoken."""
        cmd = cmd_text.strip()
        if cmd:
            self._status_indicator = "KOMUT İŞLENİYOR..."
            self.statusIndicatorChanged.emit()
            self.sendCommand(cmd)
        else:
            self._status_indicator = "SESİNİ DİNLİYORUM..."
            self.statusIndicatorChanged.emit()
            self._is_listening = True
            self.voiceStateChanged.emit(True)
            ack = "Dinliyorum, sendeyim."
            self._last_message = ack
            self.messageReceived.emit(ack)
            self.voice.speak(ack, on_finished=self._on_speech_finished)

    @Slot()
    def triggerVoiceInput(self):
        """Microphone listening and faster-whisper STT loop."""
        import threading
        if self._is_listening:
            return

        self._is_listening = True
        self.voice.is_listening_to_command = True
        self.voiceStateChanged.emit(True)
        self._last_message = "Dinliyorum, konuşabilirsin."
        self.messageReceived.emit(self._last_message)

        def _listen_worker():
            try:
                # Listen from Windows microphone for 3.5 seconds
                text = self.voice.listen_and_transcribe(duration_seconds=3.5)
                self._is_listening = False
                self.voice.is_listening_to_command = False
                self.voiceStateChanged.emit(False)

                clean_t = text.strip() if text else ""
                if clean_t and not clean_t.lower().startswith("hata") and not clean_t.lower().startswith("transkripsiyon"):
                    self.sendCommand(clean_t)
                else:
                    self._last_message = "Ses algılanmadı, dinlemeye devam ediyorum."
                    self.messageReceived.emit(self._last_message)
                    self._status_indicator = "SİSTEM ÇEVRİMİÇİ ('KİRVE' DE DİNLEYEYİM)"
                    self.statusIndicatorChanged.emit()
            except Exception:
                self._is_listening = False
                self.voice.is_listening_to_command = False
                self.voiceStateChanged.emit(False)
                self._last_message = "Seni dinliyorum."
                self.messageReceived.emit(self._last_message)
                self._status_indicator = "SİSTEM ÇEVRİMİÇİ ('KİRVE' DE DİNLEYEYİM)"
                self.statusIndicatorChanged.emit()

        threading.Thread(target=_listen_worker, daemon=True, name="KirveVoiceWorker").start()
