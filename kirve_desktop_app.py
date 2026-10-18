import sys
import os
import json
import threading
import http.server
import socketserver
import subprocess
from PySide6.QtCore import QUrl, Qt, QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QKeySequence, QIcon, QShortcut
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage

PORT = 8080
if hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(os.path.join(BASE_DIR, "kirve_cockpit.html")):
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    if os.path.exists(os.path.join(exe_dir, "kirve_cockpit.html")):
        BASE_DIR = exe_dir
    elif os.path.exists(os.path.join(os.getcwd(), "kirve_cockpit.html")):
        BASE_DIR = os.getcwd()

global_voice_engine = None
global_window = None

def free_port_if_needed(port):
    """Frees the specified port if held by a stale process."""
    try:
        res = subprocess.run(f"netstat -ano | findstr :{port}", shell=True, capture_output=True, text=True)
        current_pid = str(os.getpid())
        for line in res.stdout.strip().split("\n"):
            parts = line.strip().split()
            if len(parts) >= 5 and "LISTENING" in line:
                pid = parts[-1]
                if pid != current_pid:
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
    except Exception:
        pass

class KirveHttpHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def log_message(self, format, *args):
        pass # Silent

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/voice/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            resp = json.dumps({
                "status": "ok",
                "native_voice": True,
                "app": "KIRVE_AI_OS"
            })
            self.wfile.write(resp.encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        if self.path == "/api/voice/listen":
            # Record and transcribe from microphone using VoiceEngine
            global global_voice_engine
            transcript = ""
            if global_voice_engine:
                try:
                    global_voice_engine.is_listening_to_command = True
                    transcript = global_voice_engine.listen_and_transcribe(duration_seconds=3.5)
                except Exception as e:
                    print("listen_and_transcribe error:", e)
                finally:
                    global_voice_engine.is_listening_to_command = False

            is_wake = False
            cmd = ""
            if transcript and global_voice_engine:
                is_wake, cmd = global_voice_engine.check_wake_word(transcript)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            resp = json.dumps({
                "status": "ok",
                "transcript": transcript or "",
                "is_wake": is_wake,
                "cmd": cmd or ""
            }, ensure_ascii=False)
            self.wfile.write(resp.encode("utf-8"))
            return

        if self.path == "/api/voice/test_wake":
            global global_window
            if global_window:
                global_window.trigger_wake_test()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Wake word triggered"}).encode("utf-8"))
            return

        super().do_POST()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def start_server():
    """Start threaded server with API support."""
    free_port_if_needed(PORT)
    try:
        httpd = ThreadedTCPServer(("127.0.0.1", PORT), KirveHttpHandler)
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
    except Exception as e:
        print("start_server notice:", e)

class VoiceBridge(QObject):
    wake_detected = Signal(str)
    voice_finished = Signal(str)

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.featurePermissionRequested.connect(self.on_feature_permission)

    def on_feature_permission(self, security_origin, feature):
        self.setFeaturePermission(
            security_origin,
            feature,
            QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
        )

class KirveMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        global global_window
        global_window = self

        self.setWindowTitle("KİRVE AI OS // Kişisel Yapay Zeka İşletim Sistemi")
        self.setStyleSheet("background-color: #0A1433;")

        self.bridge = VoiceBridge()
        self.bridge.wake_detected.connect(self._handle_wake_signal)

        self.web_view = QWebEngineView(self)
        self.page = CustomWebEnginePage(self.web_view)
        self.web_view.setPage(self.page)

        # Enable features
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

        def on_loaded(ok):
            if ok:
                self.web_view.page().runJavaScript(
                    "window.isQtDesktopApp = true; window.hasNativePythonVoice = true; console.log('KİRVE Native Bridge Ready');"
                )
        self.web_view.loadFinished.connect(on_loaded)

        url = QUrl(f"http://127.0.0.1:{PORT}/kirve_cockpit.html")
        self.web_view.load(url)
        self.setCentralWidget(self.web_view)

        # Keyboard shortcuts
        self.f11_shortcut = QShortcut(QKeySequence("F11"), self)
        self.f11_shortcut.activated.connect(self.toggle_fullscreen)

        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self.exit_fullscreen)

        # Initialize Native Voice Engine
        global global_voice_engine
        try:
            from kirve.audio import VoiceEngine
            global_voice_engine = VoiceEngine()
            def _on_wake(cmd_text):
                # Thread-safe signal to Qt GUI main thread
                self.bridge.wake_detected.emit(cmd_text)
            global_voice_engine.start_wake_word_listener(_on_wake)
            print("KİRVE: Native Wake-Word listener aktif.")
        except Exception as e:
            print("Native VoiceEngine notice:", e)

        # Start in full screen
        self.showFullScreen()

    def _handle_wake_signal(self, cmd_text):
        safe_cmd = json.dumps(cmd_text, ensure_ascii=False)
        self.web_view.page().runJavaScript(f"handleWakeWord({safe_cmd});")

    def trigger_wake_test(self):
        self.bridge.wake_detected.emit("real madrid maçı hangi kanalda")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()

def main():
    start_server()
    app = QApplication(sys.argv)
    app.setApplicationName("KİRVE AI OS")

    window = KirveMainWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
