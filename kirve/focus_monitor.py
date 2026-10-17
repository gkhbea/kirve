"""
KİRVE AI OS - Focus & Fullscreen Monitor (Event Bus Integration)
Uses Windows APIs and pygetwindow to detect fullscreen games, apps, and meetings.
Automatically transitions KİRVE to silent_mode=True (Do Not Disturb / HUD only).
"""
import sys
import time
import threading
from typing import Optional, Dict, Any, List
from kirve.event_bus import EventBus, default_event_bus

# Try importing pygetwindow
try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False

# Windows native Win32 APIs
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
else:
    user32 = None

# Known meeting and game signatures
MEETING_GAME_KEYWORDS = [
    "zoom", "teams", "microsoft teams", "discord", "google meet", "webex",
    "valorant", "counter-strike", "cs2", "cyberpunk", "league of legends",
    "dota", "fortnite", "steam", "epic games", "call of duty", "gta", "minecraft"
]

class FocusMonitor:
    """
    Background window monitor that detects fullscreen applications and meetings.
    Publishes events to EventBus and toggles silent_mode accordingly.
    """
    def __init__(self, event_bus: Optional[EventBus] = None, poll_interval: float = 1.0):
        self.bus = event_bus or default_event_bus
        self.poll_interval = poll_interval
        self.silent_mode = False
        self.active_window_title = ""
        self.is_fullscreen = False
        self.is_meeting_or_game = False

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def get_screen_resolution(self) -> tuple[int, int]:
        """Gets primary screen width and height in pixels."""
        if sys.platform == "win32" and user32:
            try:
                width = user32.GetSystemMetrics(0)   # SM_CXSCREEN
                height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
                return width, height
            except Exception:
                pass
        return 1920, 1080  # Default fallback

    def inspect_active_window(self) -> Dict[str, Any]:
        """
        Inspects the current foreground window on Windows using pygetwindow and Win32.
        """
        title = ""
        rect = (0, 0, 0, 0)
        is_fs = False
        screen_w, screen_h = self.get_screen_resolution()

        if sys.platform == "win32" and user32:
            try:
                hwnd = user32.GetForegroundWindow()
                if hwnd:
                    # Get Window Title
                    length = user32.GetWindowTextLengthW(hwnd)
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value

                    # Get Window Rect
                    r = wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(r))
                    rect = (r.left, r.top, r.right, r.bottom)

                    w = r.right - r.left
                    h = r.bottom - r.top

                    # Check fullscreen condition (window bounds cover the full screen)
                    if r.left <= 0 and r.top <= 0 and r.right >= screen_w and r.bottom >= screen_h:
                        is_fs = True
                    elif w >= screen_w and h >= screen_h:
                        is_fs = True
            except Exception:
                pass

        # Also fallback or cross-reference with pygetwindow if title is empty
        if not title and PYGETWINDOW_AVAILABLE:
            try:
                active = gw.getActiveWindow()
                if active:
                    title = active.title or ""
                    rect = (active.left, active.top, active.right, active.bottom)
                    if active.width >= screen_w and active.height >= screen_h:
                        is_fs = True
            except Exception:
                pass

        # Check title for meeting or game keywords
        lower_title = title.lower()
        is_targeted = any(kw in lower_title for kw in MEETING_GAME_KEYWORDS)

        return {
            "title": title,
            "rect": rect,
            "is_fullscreen": is_fs,
            "is_meeting_or_game": is_targeted,
            "should_be_silent": is_fs or is_targeted
        }

    def check_and_update(self, mock_window_state: Optional[Dict[str, Any]] = None) -> bool:
        """
        Checks current window state, updates silent_mode, and fires events.
        mock_window_state allows deterministic testing.
        """
        state = mock_window_state or self.inspect_active_window()
        should_silence = state.get("should_be_silent", False)
        title = state.get("title", "")
        self.active_window_title = title
        self.is_fullscreen = state.get("is_fullscreen", False)
        self.is_meeting_or_game = state.get("is_meeting_or_game", False)

        if should_silence and not self.silent_mode:
            # Transition to silent mode
            self.silent_mode = True
            self.bus.publish("FULLSCREEN_ENTER", {
                "title": title,
                "is_fullscreen": self.is_fullscreen,
                "is_meeting_or_game": self.is_meeting_or_game
            })
            self.bus.publish("SILENT_MODE_CHANGED", {
                "silent_mode": True,
                "reason": f"Tam ekran/odaklanma modu aktif ({title})"
            })
            return True

        elif not should_silence and self.silent_mode:
            # Transition back to normal mode
            self.silent_mode = False
            self.bus.publish("FULLSCREEN_EXIT", {"title": title})
            self.bus.publish("SILENT_MODE_CHANGED", {
                "silent_mode": False,
                "reason": "Tam ekrandan çıkıldı, standart moda dönüldü"
            })
            return True

        return False

    def start_monitoring(self) -> None:
        """Starts background monitoring loop."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="KirveFocusMonitor")
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.check_and_update()
            except Exception:
                pass
            time.sleep(self.poll_interval)

    def stop_monitoring(self) -> None:
        """Stops background monitoring."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.5)
            self._thread = None
