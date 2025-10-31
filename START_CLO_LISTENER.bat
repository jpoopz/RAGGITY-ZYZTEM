@echo off
REM Start CLO Bridge Listener (for testing without CLO 3D)
REM This starts the listener as a standalone Python process

echo ==========================================
echo Starting CLO Bridge Listener
echo ==========================================
echo.

echo Starting listener on 127.0.0.1:51235...
echo.
echo Press Ctrl+C to stop
echo.

python modules\clo_companion\clo_bridge_listener.py

pause


