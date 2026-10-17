@echo off
chcp 65001 > nul
title KİRVE AI OS // Masaüstü HUD & Görsel Kokpit
cd /d "%~dp0"
echo ========================================================
echo    KIRVE AI OS - PySide6 & QML Fütüristik HUD Başlatılıyor...
echo ========================================================
echo.
".venv\Scripts\python.exe" run_hud.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Bir hata oluştu. Sistem Python deneniyor...
    python run_hud.py
)
pause
