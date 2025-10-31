@echo off
REM Batch wrapper for GROBID PowerShell script

echo ========================================
echo GROBID Docker Setup
echo ========================================
echo.

REM Run PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0run_grobid.ps1"

pause


