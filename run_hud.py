#!/usr/bin/env python3
"""
KİRVE AI OS - PySide6 & QML Desktop HUD Launcher
Usage: python run_hud.py
"""
import sys
from pathlib import Path
from PySide6.QtGui import QGuiApplication, QFont
from PySide6.QtQml import QQmlApplicationEngine
from kirve.gui.bridge import KirveHUDBridge

def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("KİRVE AI OS HUD")
    app.setOrganizationName("KIRVE")

    # Set default clean font
    app.setFont(QFont("DM Sans", 10))

    # Initialize bridge
    bridge = KirveHUDBridge()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)

    # Multi-path search for QML file (supports normal python, venv, and PyInstaller frozen EXE)
    candidates = []
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "kirve" / "gui" / "qml" / "main.qml")
        candidates.append(Path(sys.executable).parent / "kirve" / "gui" / "qml" / "main.qml")
    candidates.append(Path(__file__).resolve().parent / "kirve" / "gui" / "qml" / "main.qml")

    qml_file = None
    for cand in candidates:
        if cand.exists():
            qml_file = cand
            break

    if not qml_file:
        qml_file = candidates[-1]

    engine.load(str(qml_file))

    if not engine.rootObjects():
        print(f"Hata: QML arayüzü yüklenemedi: {qml_file}")
        sys.exit(-1)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
