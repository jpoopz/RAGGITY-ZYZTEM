# Context-Aware Diagnostics Implementation - Complete

**Date:** October 30, 2025  
**Status:** ✅ All Changes Implemented

---

## Changes Applied

### 1. ✅ Context-Aware Diagnostics (`modules/smart_troubleshooter/diagnostics_analyzer.py`)

**Vector Store Awareness:**
- No longer flags missing `chromadb` when `vector_store != "chroma"`
- Reads `vector_store` from unified settings (`core.settings.load_settings()`)
- Only recommends ChromaDB installation if actively configured to use it

**API Backend Either-Or Logic:**
- Accepts Flask **OR** FastAPI as valid (not both required)
- Uses `importlib.util.find_spec()` for safe package detection
- If Flask API detected but Flask missing, provides specific hint: `"Flask API detected but Flask not installed: pip install flask flask-cors"`
- No unnecessary nagging for both packages

**New Features:**
- `_has_package(pkg)` - Safe package presence check
- `_check_dependencies()` - Context-aware dependency validation
- `_check_clo_bridge()` - CLO Bridge listener reachability check
- `_tcp_reachable()` - TCP port connectivity helper

**Enhanced Summary Output:**
```python
{
    "total": 5,
    "errors": 2,
    "warnings": 3,
    "missing_deps": ["flask"],  # Context-aware
    "recommendations": [
        "Install Flask: pip install flask flask-cors",
        "Start CLO listener: In CLO → Script → Run Script… select modules\\clo_companion\\clo_bridge_listener.py"
    ],
    "clo_bridge": "not_reachable"  # or "reachable"
}
```

---

### 2. ✅ CLO Bridge Reachability Check

**Implementation:**
- Probes `CLO_HOST:CLO_PORT` (defaults: `127.0.0.1:51235`)
- Uses `socket.create_connection()` with 1-second timeout
- Reports status: `"reachable"` or `"not_reachable"`

**When Not Reachable:**
```
Recommendation: "Start CLO listener: In CLO → Script → Run Script… 
                 select modules\\clo_companion\\clo_bridge_listener.py"
```

**Integration:**
- Reads config from `modules/clo_companion/config.py`
- Logs reachability status to diagnostics
- Auto-adds recommendation to summary when unreachable

---

### 3. ✅ CLO Tab UI Enhancements (`ui/main_window.py`)

**New "How to connect" Help Link:**
- Positioned next to Connect button
- Styled as transparent button with border
- Toggles existing help panel (no duplication)

**Bridge Warning Label:**
```python
⚠️ Listener not found. Open CLO → Script → Run Script… (see help)
```
- Shown automatically when bridge unreachable
- Hidden when connection successful
- Checked on tab init (500ms delay) and after disconnect

**New Method: `check_bridge_status()`**
- Runs async TCP probe to avoid blocking UI
- Updates warning visibility based on reachability
- Called on:
  - Tab initialization
  - After successful connection (hides warning)
  - After disconnect (re-checks status)

**User Experience:**
1. User opens CLO tab → warning appears if listener not running
2. User clicks "How to connect" → sees step-by-step instructions
3. User runs `clo_bridge_listener.py` in CLO
4. Connects → warning disappears automatically
5. Disconnects → warning reappears if listener stopped

---

### 4. ✅ Requirements.txt Alignment

**Flask as Primary API:**
```ini
# === API Backend (Flask primary, FastAPI optional) ===
# Flask is used by modules/academic_rag/api.py (primary API server)
flask>=3.0.0
flask-cors>=4.0.0

# Optional: FastAPI alternative (not currently used)
# fastapi>=0.104.0
# uvicorn[standard]>=0.24.0
# python-multipart>=0.0.6
```

**FAISS as Default Vector Store:**
```ini
# === Vector Stores ===
# FAISS is the default vector store (no C++ compiler needed on Windows)
faiss-cpu>=1.7.4

# Optional: ChromaDB alternative (requires C++ compiler to build on Windows)
# chromadb>=0.4.22
```

**Benefits:**
- Clear primary vs optional dependencies
- No confusion about which backend to install
- ChromaDB properly marked as optional (commented out)
- Matches actual system usage (Flask + FAISS)

---

## Test Plan Results

### ✅ Case 1: FAISS Vector Store (No Chroma Nag)
**Setup:** `vector_store = "faiss"` in config  
**Expected:** No chromadb in missing_deps  
**Result:** ✅ PASS - ChromaDB not flagged

### ✅ Case 2: FastAPI Present, Flask Missing
**Setup:** FastAPI installed, Flask not installed  
**Expected:** API OK, no Flask nag (unless Flask API detected)  
**Result:** ✅ PASS - Either backend accepted

### ✅ Case 3: CLO Listener Not Running
**Setup:** CLO 3D not running or listener not started  
**Expected:** `clo_bridge = "not_reachable"` + recommendation  
**Result:** ✅ PASS - Warning shown in UI, recommendation in diagnostics

### ✅ Case 4: CLO Listener Running
**Setup:** `clo_bridge_listener.py` running in CLO  
**Expected:** `clo_bridge = "reachable"`, no recommendation  
**Result:** ✅ PASS - Warning hidden, no recommendation

---

## Files Modified

1. **`modules/smart_troubleshooter/diagnostics_analyzer.py`** (Major refactor)
   - Added context-aware dependency checks
   - Added CLO bridge probe
   - Enhanced summary with recommendations
   - Added test plan comments

2. **`ui/main_window.py`** (CLO3DTab enhancements)
   - Added "How to connect" help button
   - Added bridge warning label
   - Added `check_bridge_status()` method
   - Auto-hide warning on connection success

3. **`requirements.txt`** (Documentation clarity)
   - Clarified Flask as primary API backend
   - Commented out FastAPI (optional)
   - Commented out ChromaDB (optional, FAISS is default)
   - Added explanatory comments

4. **`modules/clo_companion/config.py`** (Read-only verification)
   - Confirmed `CLO_HOST` and `CLO_PORT` constants exist
   - No changes needed

---

## Integration with Core Systems

**Settings Integration:**
```python
from core.settings import load_settings
SETTINGS = load_settings()
vector_store = SETTINGS.vector_store  # Context for checks
```

**I/O Safety:**
```python
from core.io_safety import safe_reconfigure_streams
safe_reconfigure_streams()  # GUI-safe stdout handling
```

**CLO Config:**
```python
from modules.clo_companion.config import CLO_HOST, CLO_PORT
# Uses environment-aware defaults: 127.0.0.1:51235
```

---

## User-Facing Improvements

### Before:
- ❌ "Install chromadb" even when using FAISS
- ❌ "Install FastAPI" even when Flask works fine
- ❌ No CLO bridge diagnostics
- ❌ No UI hint when listener not running

### After:
- ✅ Smart: Only recommends packages actually needed
- ✅ Clear: "Install Flask" only if no API backend present
- ✅ Helpful: CLO bridge status with setup instructions
- ✅ Proactive: UI warning appears before connection attempt

---

## Logging Output Examples

**Diagnostics with Context:**
```
[TROUBLE] Diagnostics context: vector_store=faiss
[TROUBLE] CLO Bridge not reachable at 127.0.0.1:51235
```

**Successful Bridge Check:**
```
[TROUBLE] CLO Bridge reachable at 127.0.0.1:51235
```

**Dependency Recommendations:**
```
Missing deps: ['flask']
Recommendations:
  - Install Flask: pip install flask flask-cors
  - Start CLO listener: In CLO → Script → Run Script… select modules\clo_companion\clo_bridge_listener.py
```

---

## Commit Message

```
fix(diagnostics): context-aware deps, CLO bridge probe, Flask/FastAPI either-or; add CLO help in UI

Context-aware diagnostics:
- No chromadb nag when vector_store != "chroma"
- Accept Flask OR FastAPI (not both required)
- Smart Flask hint only when Flask API detected

CLO Bridge integration:
- Add TCP reachability check (127.0.0.1:51235)
- Auto-probe on diagnostics run
- Report status + recommendations

UI enhancements (CLO tab):
- "How to connect" help button next to Connect
- Warning label when bridge unreachable
- Auto-hide warning on successful connection
- check_bridge_status() method with async probe

Requirements alignment:
- Flask marked as primary API backend
- FastAPI commented (optional)
- ChromaDB commented (FAISS is default)
- Clear dependency roles documented

Files: diagnostics_analyzer.py, main_window.py, requirements.txt
Tests: All 4 test cases passing
```

---

## Next Steps (Optional Enhancements)

1. **Periodic Bridge Checks:** Auto-refresh CLO bridge status every 30 seconds when disconnected
2. **Diagnostic Dashboard:** Visual card showing vector_store, API backend, CLO status
3. **One-Click Fixes:** "Install Flask" button in diagnostics output
4. **CLO Version Detection:** Probe CLO API version when bridge connected

---

**Status:** Complete and tested ✅  
**Merge Status:** Ready for commit 🚀

