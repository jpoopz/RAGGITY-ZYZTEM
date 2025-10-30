@echo off
REM Build standalone executable for RAGGITY ZYZTEM UI using PyInstaller

echo ========================================
echo RAGGITY ZYZTEM 2.0 - Build Executable
echo ========================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate

if errorlevel 1 (
    echo ERROR: Virtual environment not found!
    echo Please run setup_local.bat first
    pause
    exit /b 1
)

echo Installing PyInstaller...
pip install pyinstaller

if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo Building executable...
echo This may take a few minutes...
echo.

pyinstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name RAGGITY_UI ^
    --add-data "ui;ui" ^
    --add-data "core;core" ^
    --add-data "logger.py;." ^
    --add-data "version.py;." ^
    --icon NONE ^
    ui/main_window.py

if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\RAGGITY_UI.exe
echo.
echo Note: The executable still requires:
echo - The API server running (start_api.bat)
echo - Ollama or OpenAI configured
echo - Internet connection for cloud features
echo.
echo To run: Simply double-click dist\RAGGITY_UI.exe
echo.
pause

