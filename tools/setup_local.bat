@echo off
REM Setup script for RAGGITY ZYZTEM 2.0 local deployment
REM Creates virtual environment and installs dependencies

echo ========================================
echo RAGGITY ZYZTEM 2.0 - Local Setup
echo ========================================
echo.

REM Check Python installation
py -3 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3 not found!
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo Python version:
py -3 --version
echo.

echo Creating virtual environment...
py -3 -m venv .venv

if not exist .venv\Scripts\activate.bat (
    echo ERROR: Failed to create virtual environment!
    pause
    exit /b 1
)

echo.
echo Activating virtual environment...
call .venv\Scripts\activate

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo WARNING: Some packages failed to install.
    echo You may need to install them manually or check requirements.txt
    echo.
) else (
    echo.
    echo ========================================
    echo Setup completed successfully!
    echo ========================================
)

echo.
echo Virtual environment created at: .venv
echo.
echo Next steps:
echo 1. Review config.yaml for configuration options
echo 2. Start API server: start_api.bat
echo 3. Launch UI: run_ui.bat
echo.
echo Optional:
echo - Set environment variables (CLO_PORT, CLOUD_URL, etc.)
echo - Configure Ollama or OpenAI settings in config.yaml
echo - Check logs in logs/ directory
echo.
pause

