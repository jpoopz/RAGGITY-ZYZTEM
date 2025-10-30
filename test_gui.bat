@echo off
REM Test GUI with visible errors (uses python.exe instead of pythonw.exe)
REM This shows error messages so we can debug why GUI isn't visible

set PYTHON_EXE=C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python312\python.exe
set APP_DIR=C:\Users\Julian Poopat\Documents\Management Class\RAG_System
set APP_SCRIPT=RAG_Control_Panel.py

cd /d "%APP_DIR%"

REM Set Tcl/Tk to match Python 3.12
set TCL_LIBRARY=C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python312\tcl\tcl8.6
set TK_LIBRARY=C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python312\tcl\tk8.6

echo ===== Testing GUI with Visible Errors =====
echo.
echo Press any key after GUI closes (or Ctrl+C to cancel)...
echo.
pause

"%PYTHON_EXE%" "%APP_SCRIPT%"

pause




