@echo off
title KIRVE AI OS Tam Ekran Kiosk
cd /d "%~dp0"

REM 1. Yerel sunucu calismiyorsa arka planda baslat
curl -s http://localhost:8080/kirve_cockpit.html >nul 2>&1
if %errorlevel% neq 0 (
    start /b "" ".venv\Scripts\python.exe" kirve_server.py >nul 2>&1
    timeout /t 1 /nobreak >nul 2>&1
)

REM 2. Tam ekran ve tarayici cubuklari olmadan ozel App modunda baslat
start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app="http://localhost:8080/kirve_cockpit.html" --start-fullscreen
exit
