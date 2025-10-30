@echo off
REM Export RAGGITY ZYZTEM 2.0 for local deployment
REM Creates a timestamped copy excluding development files

echo ========================================
echo RAGGITY ZYZTEM 2.0 - Local Export
echo ========================================
echo.

REM Generate timestamp-based folder name
set TARGET=RAGGITY_Local_%DATE:/=-%_%TIME::=-%
set TARGET=%TARGET: =_%

echo Creating export directory...
mkdir dist\%TARGET%

echo.
echo Copying files (excluding .git, .venv, node_modules, .github)...
robocopy . dist\%TARGET% /MIR /XD .git .venv node_modules .github /XF *.pyc __pycache__ .gitignore /NFL /NDL /NJH /NJS

echo.
echo ========================================
echo Export completed successfully!
echo ========================================
echo.
echo Location: dist\%TARGET%
echo.
echo Next steps:
echo 1. Navigate to dist\%TARGET%
echo 2. Run tools\setup_local.bat to install dependencies
echo 3. Use start_api.bat then run_ui.bat to launch
echo.
pause

