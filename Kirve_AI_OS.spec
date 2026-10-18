# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['kirve_desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[('kirve_cockpit.html', '.')],
    hiddenimports=['speech_recognition', 'pyaudio', 'edge_tts', 'pyttsx3', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineCore'],
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
    name='KIRVE_AI_OS',
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
    name='KIRVE_AI_OS',
)
