"""
KİRVE AI OS - Background Server with Static Serving & Native Voice API
"""
import sys
import os
import json
import threading
import http.server
import socketserver
import subprocess

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

global_voice_engine = None

def get_voice_engine():
    global global_voice_engine
    if global_voice_engine is None:
        try:
            from kirve.audio import VoiceEngine
            global_voice_engine = VoiceEngine()
        except Exception as e:
            print("VoiceEngine init notice:", e)
    return global_voice_engine

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
            self.wfile.write(json.dumps({
                "status": "ok",
                "native_voice": True,
                "app": "KIRVE_AI_OS"
            }).encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        if self.path == "/api/voice/listen":
            ve = get_voice_engine()
            transcript = ""
            if ve:
                try:
                    ve.is_listening_to_command = True
                    transcript = ve.listen_and_transcribe(duration_seconds=3.5)
                except Exception as e:
                    print("listen_and_transcribe notice:", e)
                finally:
                    ve.is_listening_to_command = False

            is_wake = False
            cmd = ""
            if transcript and ve:
                is_wake, cmd = ve.check_wake_word(transcript)

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

        super().do_POST()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_server():
    print(f"KİRVE API Sunucusu başlatılıyor: http://127.0.0.1:{PORT}")
    with ThreadedTCPServer(("127.0.0.1", PORT), KirveHttpHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
