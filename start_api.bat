@echo off
title RAGGITY ZYZTEM 2.0 - API Server
echo ========================================
echo   RAGGITY ZYZTEM 2.0 - API Server
echo ========================================
echo.

set PYTHONUTF8=1

REM Check if venv exists
if not exist .venv (
  echo [ERROR] Virtual environment not found!
  echo Please run setup.bat first.
  pause
  exit /b 1
)

echo [*] Activating virtual environment...
call .venv\Scripts\activate

echo [*] Starting FastAPI server...
echo [*] API will be available at: http://localhost:8000
echo [*] Health check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server.
echo ========================================
echo.

uvicorn rag_api:app --host 0.0.0.0 --port 8000 --reload
