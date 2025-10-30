@echo off
title RAGGITY ZYZTEM 2.0 - UI
echo ========================================
echo   RAGGITY ZYZTEM 2.0 - User Interface
echo ========================================
echo.

REM Check if venv exists
if not exist .venv (
  echo [ERROR] Virtual environment not found!
  echo Please run setup.bat first.
  pause
  exit /b 1
)

echo [*] Activating virtual environment...
call .venv\Scripts\activate

echo [*] Starting CustomTkinter UI...
echo.
python -m ui.main_window

if errorlevel 1 (
  echo.
  echo [ERROR] UI failed to start!
  echo Check logs/app.log for details.
  pause
)
