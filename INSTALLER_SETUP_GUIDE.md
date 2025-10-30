# RAG System - Installer Setup Guide

## Overview

This guide explains how to set up and use the RAG System installer package.

## Package Contents

The `Installer_Package` folder contains:

- **RAG_Control_Panel.exe** - Main GUI application (in `dist/` folder)
- **index_documents.py** - Document indexer script
- **query_llm.py** - Query processor
- **rag_api.py** - Flask API server
- **diagnostics.py** - System health checker
- **setup_dependencies.bat** - Dependency installer
- **create_shortcuts.bat** - Desktop shortcut creator
- **Documentation files** - Guides and troubleshooting docs

## Installation Steps

### Prerequisites

Before installation, ensure you have:

1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - Check "Add Python to PATH" during installation
   - Verify: Open Command Prompt, type `python --version`

2. **Ollama installed and running**
   - Download from: https://ollama.com/download
   - After installation, download Llama 3.2:
     - Open Command Prompt
     - Run: `ollama pull llama3.2`
   - Verify: Run `ollama list` to see your models

3. **Obsidian Vault**
   - Path: `C:\Users\Julian Poopat\Documents\Obsidian`
   - Notes folder: `C:\Users\Julian Poopat\Documents\Obsidian\Notes`

### Step 1: Extract Package

Extract the `Installer_Package` folder to your desired location:
```
C:\Users\Julian Poopat\Documents\Management Class\RAG_System\Installer_Package
```

### Step 2: Install Dependencies

1. Navigate to the `Installer_Package` folder
2. Double-click `setup_dependencies.bat`
3. Wait for Python packages to install (this may take a few minutes)
4. Check for any error messages

If installation fails:
- Ensure Python is in your PATH
- Try manually: `python -m pip install -r requirements.txt`

### Step 3: Create Desktop Shortcuts (Optional)

Double-click `create_shortcuts.bat` to create desktop shortcuts for:
- RAG Control Panel
- RAG API Server

### Step 4: Launch Control Panel

Double-click **RAG_Control_Panel.exe** from the `dist/` folder.

**First Launch:**
- The GUI will open
- Click "Health Check" to verify everything is ready
- Address any issues shown in red

## Using the Control Panel

### Main Features

**Status Indicators** (Top Panel):
- **Green (●)** - Component is working
- **Yellow (●)** - Component needs attention
- **Red (●)** - Component has errors
- **Gray (●)** - Component not active

**Action Buttons:**

1. **Index Documents**
   - Scans your Obsidian Notes folder
   - Creates searchable vector database
   - Takes 5-10 minutes depending on document count
   - Run this first before using queries

2. **Start API Server**
   - Starts the Flask API on http://127.0.0.1:5000
   - Required for Obsidian integration
   - Keep the control panel open while using
   - Status indicator will turn green when running

3. **Stop API Server**
   - Stops the running API server
   - Use before closing the control panel

4. **Test Query**
   - Sends a test query to verify everything works
   - Requires API server to be running

5. **Reindex Vault**
   - Re-indexes all documents
   - Use after adding new documents to your vault

6. **Health Check**
   - Runs comprehensive diagnostics
   - Checks all system components
   - Displays results in logs

7. **Open Logs Folder**
   - Opens the Logs folder
   - View operation logs for troubleshooting

### Live Logs

The log panel shows:
- Real-time operation status
- Error messages
- Diagnostic results
- API server output

Logs are also saved to `Logs/operations.log` for reference.

## Integration with Obsidian

### Configure ChatGPT MD Plugin

1. Open Obsidian
2. Go to Settings → Community Plugins → ChatGPT MD
3. Configure:
   - **API Base URL:** `http://127.0.0.1:5000/v1`
   - **Model:** `local-rag-llama3.2`
   - **API Key:** (leave empty)

Or use the enhanced system prompt method (see `CHATGPT_MD_INTEGRATION.md`).

### First Use Workflow

1. ✅ Start RAG Control Panel
2. ✅ Click "Health Check" - resolve any issues
3. ✅ Click "Index Documents" - wait for completion
4. ✅ Click "Start API Server" - keep running
5. ✅ Open Obsidian and test a query

## Troubleshooting

### Control Panel Won't Start

- **Issue:** Double-click does nothing
- **Solution:** 
  - Check if Python is installed: `python --version`
  - Try running from command line: `python RAG_Control_Panel.py`
  - Check Windows Event Viewer for errors

### Status Indicators Show Red

- **Python:** Install Python 3.8+ and ensure it's in PATH
- **Ollama:** Install from ollama.com and ensure it's in PATH
- **Llama Model:** Run `ollama pull llama3.2`
- **ChromaDB:** Run "Index Documents" first
- **Vault Path:** Verify path exists: `C:\Users\Julian Poopat\Documents\Obsidian\Notes`

### API Server Won't Start

- Check if port 5000 is already in use
- Look at logs for error messages
- Verify Python packages are installed: `pip list`
- Try starting manually: `python rag_api.py`

### Indexing Fails

- Verify Obsidian vault path exists
- Check file permissions on Notes folder
- Ensure documents are accessible (not locked by another program)
- Check logs for specific error messages

### "Dependencies Missing" Errors

1. Run `setup_dependencies.bat` again
2. Or manually: `pip install -r requirements.txt`
3. Check individual packages: `pip list | findstr chromadb`

## Auto-Start API Server (Optional)

To automatically start the API server on Windows login:

1. Press `Win + R`, type `shell:startup`, press Enter
2. Create a shortcut to `2_START_API.bat`
3. Or create a scheduled task (see Windows Task Scheduler)

## Uninstallation

To remove the RAG System:

1. Stop the API server (if running)
2. Close Control Panel
3. Delete the `Installer_Package` folder
4. Delete desktop shortcuts (if created)
5. Optional: Remove Python packages: `pip uninstall chromadb flask flask-cors pypdf2 python-docx`

**Note:** Your indexed database (`.chromadb`) and logs will remain unless manually deleted.

## Support & Documentation

- **TROUBLESHOOTING_GUIDE.md** - Detailed troubleshooting
- **CHATGPT_MD_INTEGRATION.md** - Obsidian plugin setup
- **README.md** - Complete system documentation
- **Logs/operations.log** - Operation history

## System Requirements

- **OS:** Windows 10/11
- **Python:** 3.8 or higher
- **RAM:** 4GB minimum (8GB recommended)
- **Storage:** 500MB for system + space for database
- **Internet:** Required for initial model download (Ollama)

## Next Steps

After successful installation:

1. ✅ Index your documents
2. ✅ Start API server
3. ✅ Configure Obsidian ChatGPT MD plugin
4. ✅ Test with a query
5. ✅ Start using for academic research!

---

**Need Help?** Check `TROUBLESHOOTING_GUIDE.md` or review the logs in `Logs/` folder.




