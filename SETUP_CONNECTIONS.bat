@echo off
REM Master Setup Script - Configure All Connections
REM Sets up CLO 3D Bridge and Hostinger VPS Cloud Bridge

echo ==========================================
echo Julian Assistant Suite - Connection Setup
echo ==========================================
echo.

echo This script will configure:
echo   1. CLO 3D Bridge (local TCP connection)
echo   2. Hostinger VPS Cloud Bridge (SSH + API)
echo.

pause

echo.
echo ==========================================
echo PART 1: VPS Cloud Bridge Setup
echo ==========================================
echo.

echo Setting up SSH key authentication for Hostinger VPS...
echo.

powershell -ExecutionPolicy Bypass -File remote\setup_ssh_keys.ps1

if errorlevel 1 (
    echo.
    echo ERROR: SSH key setup failed
    echo Fix the issues above and run again
    pause
    exit /b 1
)

echo.
echo SSH keys configured successfully!
echo.

echo ==========================================
echo PART 2: Deploy to VPS
echo ==========================================
echo.

set /p DEPLOY_NOW="Deploy cloud bridge to VPS now? (Y/n): "
if /i "%DEPLOY_NOW%"=="n" goto skip_deploy

powershell -ExecutionPolicy Bypass -File remote\deploy_to_vps.ps1

if errorlevel 1 (
    echo.
    echo WARNING: VPS deployment had issues
    echo You can retry later with: .\remote\deploy_to_vps.ps1
)

:skip_deploy

echo.
echo ==========================================
echo PART 3: CLO 3D Bridge Setup
echo ==========================================
echo.

echo CLO Bridge Listener Instructions:
echo.
echo 1. Open CLO 3D application
echo 2. Go to: File ^> Script ^> Run Script...
echo 3. Browse to: modules\clo_companion\clo_bridge_listener.py
echo 4. Click Run
echo.
echo You should see: "CLO Bridge Listener started on 127.0.0.1:51235"
echo.

set /p CLO_DONE="Have you started the CLO listener? (Y/n): "

echo.
echo Testing CLO bridge connection...
echo.

powershell -Command "Test-NetConnection 127.0.0.1 -Port 51235 -InformationLevel Detailed"

if errorlevel 1 (
    echo.
    echo WARNING: CLO Bridge not reachable
    echo Make sure you've run the listener script in CLO 3D
) else (
    echo.
    echo SUCCESS: CLO Bridge is responding!
)

echo.
echo ==========================================
echo PART 4: Test Connections
echo ==========================================
echo.

echo Testing VPS connection...
python -c "from core.cloud_bridge import bridge; import json; print(json.dumps(bridge.health(), indent=2))"

echo.
echo Testing CLO connection...
python -c "from modules.academic_rag.health_endpoint import get_clo_health; import json; print(json.dumps(get_clo_health(), indent=2))"

echo.
echo Testing full system health...
python -c "from modules.academic_rag.health_endpoint import get_full_health; import json; print(json.dumps(get_full_health(), indent=2))"

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.

echo Quick Reference:
echo   - Connect to VPS:  ssh hostinger-vps
echo   - CLO Listener:    Run script in CLO 3D (see above)
echo   - View Health:     python -c "from modules.academic_rag.health_endpoint import get_full_health; import json; print(json.dumps(get_full_health(), indent=2))"
echo.

echo Next Steps:
echo   1. Launch Control Panel:  python RAG_Control_Panel.py
echo   2. Enable Auto-Sync:      Cloud Bridge tab ^> Enable Auto-Sync
echo   3. Test CLO Features:     CLO 3D tab ^> Generate Garment
echo.

pause


