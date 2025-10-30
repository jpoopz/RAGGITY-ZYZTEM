@echo off
echo ========================================
echo Obsidian RAG System Setup
echo ========================================
echo.

echo Checking Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Creating directories...
if not exist "..\Notes\AI_Conversations" mkdir "..\Notes\AI_Conversations"
if not exist "..\Notes\Web_Imports" mkdir "..\Notes\Web_Imports"

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run: python index_documents.py
echo 2. Run: python rag_api.py
echo.
pause




