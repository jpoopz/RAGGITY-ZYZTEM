@echo off
REM Launch Julian Assistant Suite with Docker

echo Starting Julian Assistant Suite with Docker...
cd /d "%~dp0"

docker-compose -f docker/docker-compose.yml up -d

echo.
echo Services starting...
echo Check status with: docker-compose -f docker/docker-compose.yml ps
echo Stop with: stop_docker.bat
echo.

timeout /t 3
start http://127.0.0.1:5000/health

pause




