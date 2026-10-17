# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_hud.py'],
    pathex=[],
    binaries=[],
    datas=[('kirve/gui/qml/main.qml', 'kirve/gui/qml')],
    hiddenimports=['PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.QtCore', 'PySide6.QtGui', 'psutil', 'pygetwindow', 'pyttsx3', 'pyttsx3.drivers.sapi5', 'pythoncom', 'win32com.client', 'kirve.conversational', 'speech_recognition', 'pyaudio', 'edge_tts'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Kirve_AI_OS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Kirve_AI_OS',
)
