@echo off
REM RAG Academic Assistant - Desktop Launcher
REM Launches GUI exactly as Cursor does

REM Set exact paths
set PYTHONW_EXE=C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python312\pythonw.exe
set APP_DIR=C:\Users\Julian Poopat\Documents\Management Class\RAG_System
set APP_SCRIPT=RAG_Control_Panel.py
set LOG_DIR=%APP_DIR%\Logs
set LOG_FILE=%LOG_DIR%\launch.log
set DEBUG_FILE=%APP_DIR%\debug_launch.log

REM Create logs directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Debug logging
echo [%date% %time%] ===== Launch Attempt ===== > "%DEBUG_FILE%"
echo Python: %PYTHONW_EXE% >> "%DEBUG_FILE%"
echo Directory: %APP_DIR% >> "%DEBUG_FILE%"
echo Script: %APP_SCRIPT% >> "%DEBUG_FILE%"
echo Current Dir: %CD% >> "%DEBUG_FILE%"

REM Change to application directory (critical!)
cd /d "%APP_DIR%"
if errorlevel 1 (
    echo ERROR: Failed to change directory >> "%DEBUG_FILE%"
    echo [%date% %time%] ERROR: Failed to change directory >> "%LOG_FILE%"
    exit /b 1
)
echo Changed to: %CD% >> "%DEBUG_FILE%"

REM Verify files exist
if not exist "%APP_SCRIPT%" (
    echo ERROR: Script not found >> "%DEBUG_FILE%"
    echo [%date% %time%] ERROR: %APP_SCRIPT% not found >> "%LOG_FILE%"
    exit /b 1
)

if not exist "%PYTHONW_EXE%" (
    echo WARNING: pythonw.exe not at expected path >> "%DEBUG_FILE%"
    echo Trying pythonw from PATH... >> "%DEBUG_FILE%"
    where pythonw.exe >> "%DEBUG_FILE%" 2>&1
    set PYTHONW_EXE=pythonw.exe
)

REM Set Tcl/Tk environment variables (must match Python 3.12)
set TCL_LIBRARY=C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python312\tcl\tcl8.6
set TK_LIBRARY=C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python312\tcl\tk8.6
echo TCL_LIBRARY=%TCL_LIBRARY% >> "%DEBUG_FILE%"
echo TK_LIBRARY=%TK_LIBRARY% >> "%DEBUG_FILE%"

REM Log launch
echo [%date% %time%] Launching via desktop shortcut >> "%LOG_FILE%"
echo Launching command: "%PYTHONW_EXE%" "%APP_SCRIPT%" >> "%DEBUG_FILE%"

REM Capture Python errors to log file
set ERROR_LOG=%APP_DIR%\Logs\python_errors.log

REM Launch GUI using start command
REM /B = start without new window (for pythonw.exe which already runs windowed)
REM pythonw.exe will show its own window, errors go to log
start "" /B "%PYTHONW_EXE%" "%APP_SCRIPT%" 2>> "%ERROR_LOG%"

REM pythonw.exe returns immediately, so exit code isn't reliable
REM But we log the launch attempt
echo Launch command executed >> "%DEBUG_FILE%"
echo [%date% %time%] Launch command executed >> "%LOG_FILE%"

REM Exit immediately
exit /b 0
