@echo off
chcp 65001 > nul
title KİRVE AI OS // Kişisel Yapay Zeka İşletim Sistemi
cd /d "%~dp0"
echo ========================================================
echo    KIRVE AI OS - Komut Satiri Kokpiti Baslatiliyor...
echo ========================================================
echo.
".venv\Scripts\python.exe" run.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Bir hata olustu. Sistem Python deneniyor...
    python run.py
)
pause
