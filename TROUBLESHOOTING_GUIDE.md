# RAG System - Troubleshooting Guide

## Quick Diagnosis

### Step 1: Run Health Check

In the Control Panel, click **"Health Check"** and review the results. This will identify most common issues.

### Step 2: Check Logs

Click **"Open Logs Folder"** and review `operations.log` for error messages.

---

## Common Issues & Solutions

### 🔴 Issue: "Python not found" or Python status shows red

**Symptoms:**
- Control Panel won't start
- Status indicator shows red
- Error: "python is not recognized"

**Solutions:**

1. **Verify Python installation:**
   ```
   Open Command Prompt → python --version
   ```
   If this fails, Python is not in PATH.

2. **Install Python:**
   - Download from https://www.python.org/downloads/
   - During installation, **check "Add Python to PATH"**
   - Restart Command Prompt after installation

3. **Manually add to PATH:**
   - Find Python installation (usually `C:\Python3x\` or `C:\Users\...\AppData\Local\Programs\Python\`)
   - Add to Windows PATH:
     - Press `Win + X` → System → Advanced System Settings
     - Environment Variables → Path → Edit → Add Python path
   - Restart computer

---

### 🔴 Issue: "Ollama not found" or Ollama status shows red

**Symptoms:**
- Ollama indicator red
- Cannot start API server
- Error running queries

**Solutions:**

1. **Install Ollama:**
   - Download from https://ollama.com/download
   - Install and ensure it's added to PATH
   - Restart Command Prompt

2. **Verify installation:**
   ```
   ollama --version
   ollama list
   ```

3. **Start Ollama service:**
   - Ollama should start automatically after installation
   - Or run: `ollama serve`
   - Check if port 11434 is accessible

---

### 🟡 Issue: "Llama model not found"

**Symptoms:**
- Ollama is green, but Llama is yellow/red
- Queries fail with "model not found"

**Solutions:**

1. **Download Llama 3.2:**
   ```
   ollama pull llama3.2
   ```
   This downloads ~2GB, takes 5-10 minutes.

2. **Verify download:**
   ```
   ollama list
   ```
   Should show `llama3.2` in the list.

3. **Try alternative models:**
   - `ollama pull llama3` (if llama3.2 unavailable)
   - Update model name in `query_llm.py` if needed

---

### 🟡 Issue: "ChromaDB not found" or yellow status

**Symptoms:**
- ChromaDB indicator yellow
- "No database found" errors
- Queries return no results

**Solutions:**

1. **Run indexing:**
   - In Control Panel, click **"Index Documents"**
   - Wait for completion (5-10 minutes)
   - Status should turn green

2. **Verify indexing:**
   - Check `.chromadb` folder exists in RAG_System directory
   - Should contain database files

3. **Reindex if needed:**
   - Click **"Reindex Vault"** in Control Panel
   - Ensures all documents are indexed

---

### 🔴 Issue: "Missing Python packages" errors

**Symptoms:**
- Import errors when starting scripts
- "No module named 'chromadb'" errors

**Solutions:**

1. **Install dependencies:**
   - Run `setup_dependencies.bat` in Installer_Package
   - Or manually: `pip install -r requirements.txt`

2. **Install individual packages:**
   ```
   pip install chromadb flask flask-cors pypdf2 python-docx requests numpy
   ```

3. **Check installation:**
   ```
   pip list | findstr chromadb
   ```

4. **Upgrade pip:**
   ```
   python -m pip install --upgrade pip
   ```

---

### 🔴 Issue: "API server won't start" or port 5000 in use

**Symptoms:**
- API indicator stays gray
- "Address already in use" error
- Cannot start API server

**Solutions:**

1. **Check if port is already in use:**
   ```
   netstat -ano | findstr :5000
   ```
   If something is using port 5000, stop it first.

2. **Stop existing process:**
   - Find PID from netstat command
   - Open Task Manager → Details tab
   - Find process with that PID and end it
   - Or restart computer

3. **Use different port:**
   - Edit `rag_api.py`:
     ```python
     app.run(host='127.0.0.1', port=5001, debug=False)
     ```
   - Update Obsidian plugin URL to `http://127.0.0.1:5001/v1`

4. **Check firewall:**
   - Windows Firewall may block port 5000
   - Allow through firewall or disable temporarily for testing

---

### 🟡 Issue: "Vault path not found"

**Symptoms:**
- Vault indicator yellow/red
- "Path not found" errors
- Indexing fails

**Solutions:**

1. **Verify vault exists:**
   - Check: `C:\Users\Julian Poopat\Documents\Obsidian`
   - Should contain `Notes` folder

2. **Update path if different:**
   - Edit `index_documents.py`:
     ```python
     VAULT_PATH = r"C:\Your\Actual\Path\Obsidian"
     ```
   - Edit `query_llm.py` with same path
   - Restart Control Panel

3. **Create structure if missing:**
   - Create `Obsidian` folder if needed
   - Create `Notes` subfolder
   - Add some test documents (.md files)

---

### 🔴 Issue: "Indexing fails" or hangs

**Symptoms:**
- Indexing starts but never completes
- Errors during indexing
- Process appears frozen

**Solutions:**

1. **Check document count:**
   - Too many documents (>10,000) may take very long
   - Check logs for progress

2. **Check file permissions:**
   - Ensure Notes folder is not read-only
   - Right-click folder → Properties → Uncheck Read-only

3. **Check disk space:**
   - Indexing creates database that can be 100MB+
   - Ensure sufficient free space

4. **Try individual files:**
   - Move most files temporarily
   - Index a few files first
   - Add more gradually

5. **Check for corrupted files:**
   - PDFs or DOCX files may be corrupted
   - Remove problematic files and retry

---

### 🟡 Issue: "Queries return no results" or empty responses

**Symptoms:**
- API server running
- Queries succeed but return no useful results
- Citations are empty

**Solutions:**

1. **Verify indexing completed:**
   - Check ChromaDB status (should be green)
   - Verify `.chromadb` folder has files

2. **Check query similarity:**
   - Try very specific queries matching document content
   - Example: if document mentions "strategic management", query for that exact phrase

3. **Reindex with more documents:**
   - More documents = better search results
   - Ensure documents are in Notes folder

4. **Check document format:**
   - Ensure documents are readable (not corrupted)
   - PDFs should have selectable text (not scanned images)

---

### 🔴 Issue: "Control Panel crashes" or freezes

**Symptoms:**
- GUI stops responding
- Application closes unexpectedly
- Error dialogs appear

**Solutions:**

1. **Check Windows Event Viewer:**
   - Press `Win + X` → Event Viewer
   - Look for error entries related to Python

2. **Update Python:**
   - Older Python versions may have issues
   - Upgrade to Python 3.10 or 3.11

3. **Run from command line:**
   ```
   python RAG_Control_Panel.py
   ```
   - See full error messages
   - Report errors for debugging

4. **Check available RAM:**
   - Control Panel uses minimal RAM
   - But indexing needs 2-4GB free
   - Close other applications

---

### 🟡 Issue: "Obsidian plugin won't connect"

**Symptoms:**
- ChatGPT MD plugin shows connection errors
- Cannot send queries from Obsidian

**Solutions:**

1. **Verify API server running:**
   - Check Control Panel - API indicator should be green
   - Test: Open browser → `http://127.0.0.1:5000/health`

2. **Check plugin configuration:**
   - API URL: `http://127.0.0.1:5000/v1`
   - Model: `local-rag-llama3.2`
   - API Key: (empty)

3. **Test API directly:**
   ```
   curl -X POST http://127.0.0.1:5000/query -H "Content-Type: application/json" -d "{\"query\":\"test\"}"
   ```
   Or use PowerShell:
   ```powershell
   $body = @{query="test"} | ConvertTo-Json
   Invoke-RestMethod -Uri "http://127.0.0.1:5000/query" -Method POST -Body $body -ContentType "application/json"
   ```

4. **Check CORS settings:**
   - Verify `flask-cors` is installed
   - Should be enabled in `rag_api.py`

---

## Advanced Troubleshooting

### Enable Debug Logging

Edit `rag_api.py`:
```python
app.run(host='127.0.0.1', port=5000, debug=True)
```

### Test Individual Components

1. **Test Python:**
   ```python
   python -c "import sys; print(sys.version)"
   ```

2. **Test Ollama:**
   ```
   ollama run llama3.2 "Hello"
   ```

3. **Test ChromaDB:**
   ```python
   python -c "import chromadb; print('OK')"
   ```

4. **Test Flask:**
   ```python
   python -c "import flask; print('OK')"
   ```

### Manual API Start

If Control Panel fails, start API manually:
```
cd "C:\Users\Julian Poopat\Documents\Management Class\RAG_System"
python rag_api.py
```

Check output for errors.

---

## Getting Help

If issues persist:

1. **Review logs:**
   - `Logs/operations.log` - Control Panel logs
   - Console output from API server

2. **Collect information:**
   - Python version: `python --version`
   - Ollama version: `ollama --version`
   - OS version: `winver`
   - Error messages from logs

3. **Check documentation:**
   - `README.md` - Complete system docs
   - `INSTALLER_SETUP_GUIDE.md` - Setup instructions

---

## Prevention Tips

1. **Regular health checks:**
   - Run "Health Check" weekly
   - Address yellow indicators promptly

2. **Backup database:**
   - Copy `.chromadb` folder periodically
   - Prevents loss if corruption occurs

3. **Update dependencies:**
   - Update Python packages monthly: `pip install --upgrade -r requirements.txt`
   - Keep Ollama updated

4. **Monitor logs:**
   - Check `Logs/operations.log` regularly
   - Identify issues early

---

**Remember:** Most issues are resolved by running "Health Check" in the Control Panel and following its recommendations!




