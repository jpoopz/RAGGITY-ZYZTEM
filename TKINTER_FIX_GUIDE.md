# Tkinter TclError Fix Guide

## Problem
Getting `TclError: Can't find a usable init.tcl` when launching RAG_Control_Panel.py

## Root Cause
Python 3.14 installation may not include Tcl/Tk libraries, or they're in a non-standard location.

## Solution 1: Reinstall Python with Tcl/Tk (Recommended)

1. **Download Python 3.14 from python.org:**
   - Go to: https://www.python.org/downloads/
   - Download Python 3.14.x Windows installer

2. **During Installation:**
   - ✅ Check "Add Python to PATH"
   - ✅ **IMPORTANT:** Check "tcl/tk and IDLE" option
   - Install to default location or: `C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python314`

3. **Verify Installation:**
   - Open Command Prompt
   - Run: `python -c "import tkinter; tkinter._test()"`
   - Should open a test window

## Solution 2: Manual Tcl/Tk Installation

If Python is already installed without Tcl/Tk:

### Option A: Install via ActiveState (Easiest)

1. Download ActiveState Tcl/Tk:
   - https://www.activestate.com/products/tcl/
   - Or search: "ActiveState Tcl/Tk Windows download"

2. Install to:
   ```
   C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python314\tcl\
   ```

3. Structure should be:
   ```
   Python314\
   └── tcl\
       ├── tcl8.6\
       │   └── init.tcl
       └── tk8.6\
           └── tk.tcl
   ```

### Option B: Extract from Python Build

1. Find a Python installation with Tcl/Tk (even older version)
2. Copy the `tcl` folder from that installation
3. Paste into: `C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python314\`

## Solution 3: Use Environment Variables

If Tcl/Tk exists but in different location:

1. **Find your Tcl/Tk directories:**
   ```powershell
   Get-ChildItem "C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python314" -Recurse -Filter "init.tcl"
   ```

2. **Set environment variables:**
   ```powershell
   [Environment]::SetEnvironmentVariable("TCL_LIBRARY", "C:\...\tcl8.6", "User")
   [Environment]::SetEnvironmentVariable("TK_LIBRARY", "C:\...\tk8.6", "User")
   ```

3. **Restart PowerShell/Command Prompt**

## Solution 4: Use Alternative GUI (Temporary Workaround)

If Tkinter can't be fixed immediately, we can create a web-based GUI instead using Flask.

## Quick Test

After applying any solution, test:

```python
import tkinter
tkinter._test()
```

Should open a test window with buttons.

## Updated RAG_Control_Panel.py

The updated `RAG_Control_Panel.py` now includes auto-detection of Tcl/Tk paths. It will:
1. Search for Tcl/Tk in standard locations
2. Set environment variables automatically
3. Provide clearer error messages

## Files Created

- `fix_tkinter_complete.py` - Automated fix script
- `LAUNCH_GUI.bat` - Launcher with path fixes
- This guide

---

**Quick Fix:** Run `python fix_tkinter_complete.py` first!




