@echo off
chcp 65001 > nul
title KİRVE AI OS // Tek Tık EXE Paketleyici
cd /d "%~dp0"
echo ========================================================
echo    KIRVE AI OS - Tek Tık Standalone EXE Oluşturuluyor...
echo ========================================================
echo.

if not exist ".venv\Scripts\pyinstaller.exe" (
    echo PyInstaller kuruluyor...
    ".venv\Scripts\pip.exe" install pyinstaller
)

echo QML ve PySide6 bilesenleri paketleniyor...
".venv\Scripts\pyinstaller.exe" --noconfirm ^
    --onedir ^
    --windowed ^
    --name "Kirve_AI_OS" ^
    --add-data "kirve/gui/qml/main.qml;kirve/gui/qml" ^
    --hidden-import "PySide6.QtQuick" ^
    --hidden-import "PySide6.QtQml" ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "psutil" ^
    --hidden-import "pygetwindow" ^
    --hidden-import "pyttsx3" ^
    --hidden-import "pyttsx3.drivers.sapi5" ^
    --hidden-import "pythoncom" ^
    --hidden-import "win32com.client" ^
    --hidden-import "kirve.conversational" ^
    --hidden-import "speech_recognition" ^
    --hidden-import "pyaudio" ^
    run_hud.py

if %ERRORLEVEL% EQU 0 (
    powershell -NoProfile -Command "New-Item -ItemType Directory -Force -Path 'dist\Kirve_AI_OS\kirve\gui\qml' -ErrorAction SilentlyContinue; Copy-Item -Force 'kirve\gui\qml\main.qml' 'dist\Kirve_AI_OS\kirve\gui\qml\'"
    echo.
    echo ========================================================
    echo    TEK TIK EXE BASARIYLA OLUSTURULDU!
    echo    Konum: dist\Kirve_AI_OS\Kirve_AI_OS.exe
    echo ========================================================
    echo.
    echo Masaustune kisayol olusturuluyor...
    powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'KIRVE AI OS.lnk')); $s.TargetPath = [System.IO.Path]::Combine((Get-Location).Path, 'dist', 'Kirve_AI_OS', 'Kirve_AI_OS.exe'); $s.WorkingDirectory = [System.IO.Path]::Combine((Get-Location).Path, 'dist', 'Kirve_AI_OS'); $s.Description = 'KIRVE AI OS - Standalone Masaustu HUD'; $s.Save()"
    echo Masaustu kisayolu hazir!
) else (
    echo.
    echo [HATA] EXE olusturma sirasinda bir hata meydana geldi.
)

pause
