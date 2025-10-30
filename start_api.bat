@echo off
echo ========================================
echo Starting Obsidian RAG API Server
echo ========================================
echo.

cd /d "%~dp0"

echo Checking if API is already running...
netstat -ano | findstr :5000 >nul
if %errorlevel% equ 0 (
    echo API server is already running on port 5000
    echo Please stop it first or use a different port
    pause
    exit /b 1
)

echo.
echo Starting API server...
echo API will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python rag_api.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start API server
    echo Make sure dependencies are installed: pip install -r requirements.txt
    pause
)




