# Julian Assistant Suite - Smart Launcher Guide

**Version:** v7.8.0-Julian-SmartLauncher

## 🚀 Quick Start

Double-click the **"Julian Assistant Suite"** shortcut on your Desktop to launch the application.

## 📋 What the Launcher Does

The smart launcher (`LAUNCH_ASSISTANT.py`) performs the following steps:

1. **Splash Screen** - Displays initialization progress
2. **Python Check** - Verifies Python 3.8+ is installed
3. **Tkinter Check** - Ensures GUI library is available
4. **Dependency Check** - Scans for required packages:
   - flask
   - chromadb
   - fastapi
   - uvicorn
   - requests
   - pillow
5. **Auto-Install** - Installs any missing packages automatically
6. **Launch GUI** - Starts the Control Panel
7. **API Checks** - Verifies RAG API (port 5000) and CLO API (port 5001) are responding
8. **Logging** - Records all actions to `Logs/launcher.log`

## 🎨 Splash Screen

The launcher displays a minimal splash screen during initialization:

- **Size:** 400x250 pixels
- **Theme:** Dark background (#1a1a1a)
- **Elements:**
  - Title: "Julian Assistant Suite" (green)
  - Status text: Current initialization step
  - Version number
  - Progress bar (indeterminate)

The splash automatically closes after the Control Panel fully loads.

## 📁 Files

- **LAUNCH_ASSISTANT.py** - Main launcher script
- **assets/julian_assistant.ico** - Application icon
- **assets/generate_icon.py** - Icon generator
- **create_shortcut.ps1** - Shortcut creation script
- **Logs/launcher.log** - Launch logs

## 🔍 Troubleshooting

### Launcher Logs

Check `Logs/launcher.log` for detailed startup information:

```
[2025-01-XX XX:XX:XX] [INFO] Julian Assistant Suite Launcher Starting
[2025-01-XX XX:XX:XX] [INFO] Python 3.12.0 ✓
[2025-01-XX XX:XX:XX] [INFO] tkinter available ✓
[2025-XX-XX XX:XX:XX] [INFO] All dependencies installed ✓
[2025-XX-XX XX:XX:XX] [INFO] ✅ Launch successful
```

### Common Issues

**GUI doesn't start:**
- Check Python version: `python --version` (should be 3.8+)
- Verify tkinter: `python -c "import tkinter"`
- Review `Logs/launcher.log` for errors

**Dependencies missing:**
- Launcher will auto-install, but check logs if it fails
- Manually install: `pip install flask chromadb fastapi uvicorn requests pillow`

**Splash screen stuck:**
- Check if Control Panel process is running
- Review `Logs/launcher.log` for errors
- Try launching `RAG_Control_Panel.py` directly for debugging

**API health checks fail:**
- This is normal if APIs aren't started yet
- APIs can be started manually from the Control Panel
- Non-blocking checks won't prevent launch

## 🖥️ Desktop Shortcut

The desktop shortcut is configured with:

- **Name:** Julian Assistant Suite
- **Target:** `pythonw.exe LAUNCH_ASSISTANT.py`
- **Working Directory:** RAG_System folder
- **Icon:** `assets/julian_assistant.ico`
- **Description:** "Launch Julian Assistant Suite - AI Control Hub"

## 🔄 Recreating the Shortcut

If the shortcut is missing or needs to be recreated:

```powershell
cd "C:\Users\Julian Poopat\Documents\Management Class\RAG_System"
powershell -ExecutionPolicy Bypass -File "create_shortcut.ps1"
```

## ✅ Success Indicators

After successful launch, you should see:

1. Splash screen appears briefly
2. Control Panel window opens
3. `Logs/launcher.log` contains "✅ Launch successful"
4. No error dialogs

## 📊 Version

**Current Version:** v7.8.0-Julian-SmartLauncher

---

*For more information, see the main Julian Assistant Suite documentation.*




