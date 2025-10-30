@echo off
REM Stop Julian Assistant Suite Docker services

echo Stopping Julian Assistant Suite services...
cd /d "%~dp0"

docker-compose -f docker/docker-compose.yml down

echo.
echo Services stopped.
echo.

pause




