@echo off
REM Simple wrapper to run PowerShell script
echo Creating desktop shortcut for RAGGITY ZYZTEM UI...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0create_ui_shortcut.ps1"
echo.
pause

