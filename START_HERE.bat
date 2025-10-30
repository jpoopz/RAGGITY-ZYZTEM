@echo off
REM Quick start script for RAG System
REM Double-click this file to open command prompt in the right directory

cd /d "%~dp0"
echo ========================================
echo   RAG System - Quick Start
echo ========================================
echo.
echo Current directory: %CD%
echo.
echo Available commands:
echo   1. Index documents:        python index_documents.py
echo   2. Start API server:        python rag_api.py
echo   3. Test query:              python query_helper.py query "your question"
echo   4. Test endpoints:          .\test_all_endpoints.ps1
echo.
echo ========================================
echo.

REM Keep window open
cmd /k




