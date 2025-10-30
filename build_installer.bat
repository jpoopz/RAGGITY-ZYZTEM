@echo off
REM Build script for creating Windows installer package
REM Packages RAG System into distributable format

echo ========================================
echo   RAG System - Build Installer
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
set BUILD_DIR=%SCRIPT_DIR%Installer_Package
set DIST_DIR=%BUILD_DIR%\dist

REM Create build directories
echo Creating build directories...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"
mkdir "%DIST_DIR%"
mkdir "%BUILD_DIR%\logs"

REM Check if PyInstaller is installed
echo Checking PyInstaller...
python -m pip install pyinstaller --quiet
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

REM Build executable from control panel
echo.
echo Building RAG Control Panel executable...
pyinstaller --name="RAG_Control_Panel" ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data "diagnostics.py;." ^
    --hidden-import=diagnostics ^
    --hidden-import=chromadb ^
    --hidden-import=flask ^
    --hidden-import=requests ^
    RAG_Control_Panel.py

if errorlevel 1 (
    echo PyInstaller build failed!
    pause
    exit /b 1
)

REM Move executable to dist folder
if exist "dist\RAG_Control_Panel.exe" (
    copy "dist\RAG_Control_Panel.exe" "%DIST_DIR%\"
    echo Executable created successfully!
) else (
    echo Executable not found! Build may have failed.
    pause
    exit /b 1
)

REM Copy necessary files
echo.
echo Copying files to package...
copy "index_documents.py" "%BUILD_DIR%\"
copy "query_llm.py" "%BUILD_DIR%\"
copy "rag_api.py" "%BUILD_DIR%\"
copy "query_helper.py" "%BUILD_DIR%\"
copy "diagnostics.py" "%BUILD_DIR%\"

REM Copy documentation
if exist "README.md" copy "README.md" "%BUILD_DIR%\"
if exist "INSTALLER_SETUP_GUIDE.md" copy "INSTALLER_SETUP_GUIDE.md" "%BUILD_DIR%\"
if exist "TROUBLESHOOTING_GUIDE.md" copy "TROUBLESHOOTING_GUIDE.md" "%BUILD_DIR%\"
if exist "CHATGPT_MD_INTEGRATION.md" copy "CHATGPT_MD_INTEGRATION.md" "%BUILD_DIR%\"

REM Copy batch files
copy "1_INDEX.bat" "%BUILD_DIR%\"
copy "2_START_API.bat" "%BUILD_DIR%\"

REM Create requirements.txt if missing
if not exist "requirements.txt" (
    echo Creating requirements.txt...
    (
        echo chromadb
        echo flask
        echo flask-cors
        echo pypdf2
        echo python-docx
        echo requests
        echo beautifulsoup4
        echo numpy
        echo tqdm
    ) > "%BUILD_DIR%\requirements.txt"
) else (
    copy "requirements.txt" "%BUILD_DIR%\"
)

REM Create setup script
echo.
echo Creating setup script...
(
    echo @echo off
    echo REM RAG System Setup Script
    echo echo Installing Python dependencies...
    echo python -m pip install --upgrade pip
    echo python -m pip install -r requirements.txt
    echo echo.
    echo echo Setup complete! You can now run RAG_Control_Panel.exe
    echo pause
) > "%BUILD_DIR%\setup_dependencies.bat"

REM Create README for installer package
echo.
echo Creating package README...
(
    echo ========================================
    echo   RAG System - Installation Package
    echo ========================================
    echo.
    echo QUICK START:
    echo.
    echo 1. Run setup_dependencies.bat ^(installs Python packages^)
    echo 2. Double-click RAG_Control_Panel.exe
    echo 3. Click "Index Documents"
    echo 4. Click "Start API Server"
    echo 5. Start using in Obsidian!
    echo.
    echo REQUIREMENTS:
    echo - Python 3.8+ installed
    echo - Ollama installed and running
    echo - Llama 3.2 model downloaded
    echo.
    echo For detailed instructions, see INSTALLER_SETUP_GUIDE.md
    echo.
) > "%BUILD_DIR%\PACKAGE_README.txt"

REM Create desktop shortcuts script (for installer)
echo.
echo Creating shortcuts script...
(
    echo @echo off
    echo REM Create desktop shortcuts
    echo set SCRIPT_DIR=%%~dp0
    echo.
    echo REM Shortcut for Control Panel
    echo powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%%USERPROFILE%%\Desktop\RAG Control Panel.lnk'^); $Shortcut.TargetPath = '%%SCRIPT_DIR%%dist\RAG_Control_Panel.exe'; $Shortcut.WorkingDirectory = '%%SCRIPT_DIR%%'; $Shortcut.Description = 'RAG System Control Panel'; $Shortcut.Save()"
    echo.
    echo REM Shortcut for API Server
    echo powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%%USERPROFILE%%\Desktop\RAG API Server.lnk'^); $Shortcut.TargetPath = '%%SCRIPT_DIR%%2_START_API.bat'; $Shortcut.WorkingDirectory = '%%SCRIPT_DIR%%'; $Shortcut.Description = 'Start RAG API Server'; $Shortcut.Save()"
    echo.
    echo Shortcuts created on desktop!
    echo pause
) > "%BUILD_DIR%\create_shortcuts.bat"

echo.
echo ========================================
echo   BUILD COMPLETE!
echo ========================================
echo.
echo Package created at:
echo %BUILD_DIR%
echo.
echo Next steps:
echo 1. Test RAG_Control_Panel.exe in dist folder
echo 2. Create installer using Inno Setup ^(optional^)
echo 3. Distribute the Installer_Package folder
echo.
pause




