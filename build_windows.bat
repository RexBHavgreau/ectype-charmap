@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher was not found. Install Python 3 and try again.
    pause
    exit /b 1
)

py -3 -m pip install --upgrade pyinstaller
if errorlevel 1 goto build_failed

py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name EctypeCharmap main.py
if errorlevel 1 goto build_failed

echo.
echo Build complete: dist\EctypeCharmap.exe
pause
exit /b 0

:build_failed
echo.
echo Build failed. Check the error above and try again.
pause
exit /b 1