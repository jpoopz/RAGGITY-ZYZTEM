@echo off
title RAG System - Index Documents
color 0A
echo.
echo ========================================
echo   INDEXING YOUR DOCUMENTS
echo ========================================
echo.
echo This will scan your Notes folder and create
echo a searchable index of all documents.
echo.
echo Press any key to start...
pause > nul
echo.
python index_documents.py
echo.
echo ========================================
echo   INDEXING COMPLETE!
echo ========================================
echo.
echo Next step: Double-click 2_START_API.bat
echo.
pause




