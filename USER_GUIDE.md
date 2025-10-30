# Julian Assistant Suite - User Guide

**Version:** 3.0.0  
**Last Updated:** 2025-10-29

---

## 🚀 **Quick Start**

### First Launch

1. **Double-click** desktop shortcut: `RAG Academic Assistant.lnk`
2. **GUI opens** with Dashboard tab active
3. **System auto-starts** Academic RAG module (5-second delay)
4. **Check status:** All module indicators should turn green

---

## 📊 **Dashboard Tab**

### System Metrics

- **CPU Bar:** Real-time CPU usage percentage
- **RAM Bar:** Real-time RAM usage percentage
- **GPU Bar:** GPU usage (if available, requires nvidia-smi)

### Quick Actions

- **Full System Test:** Tests all module `/health` endpoints
  - ✅ Green: Module responding
  - ⚠️ Yellow: Module degraded
  - ❌ Red: Module not responding

### Module Status

Shows all registered modules with current status:
- `healthy` - Module running and responding
- `degraded` - Module has issues
- `unhealthy` - Module not responding
- `stopped` - Module not started

---

## 📚 **RAG & Docs Tab**

### Query Interface

1. **Enter query** in text field (e.g., "What is strategic management?")
2. **Click "Query"** button
3. **Response appears** in text area below
4. **Citations included** inline: `[Source: filename, lines X-Y]`

### Context Preview

- **Click "Show Preview"** to see what context will be sent to LLM
- Shows:
  - Memory facts (preferences, learned info)
  - RAG documents (retrieved from vault)
  - System status
  - Recent voice commands
  - Active CLO project

---

## 🧵 **CLO Companion Tab**

### Generate Garment

1. **Enter prompt:** "Generate short-sleeve shirt pattern"
2. **Click "Generate"** button
3. **Result:** OBJ file path and pattern JSON
4. **Preview:** Click "Preview Latest" to view most recent garment

### Example Prompts

- "Generate shirt pattern"
- "Create dress with pleats"
- "Make jacket pattern"
- "Generate garment: long-sleeve top"

---

## 🎤 **Voice & Automation Tab**

### Enable Voice Control

1. **Toggle "Enable Voice Control"** switch
2. **Status changes** to "Enabled (Press F9)"
3. **Press F9** (hold while speaking)
4. **Say command** (e.g., "start rag api")
5. **Release F9** when done

### Edit Commands

1. **Click "Edit Commands"** button
2. **Edit JSON** in popup window
3. **Click "Save"** to apply changes
4. **Commands reload** automatically

### Supported Commands

- `"start rag api"` - Start Academic RAG API
- `"index documents"` - Index vault documents
- `"health check"` - Run system health check
- `"generate shirt"` - Generate garment in CLO
- `"switch low power"` - Switch to CPU-only mode
- And more (fully customizable)

### Custom Commands

Add your own in `commands.json`:

```json
{
  "commands": {
    "your custom phrase": {
      "action": "system.your_action",
      "description": "What this command does"
    }
  }
}
```

---

## ⚙️ **Settings & Profiles Tab**

### Profiles

**Academic** (Default)
- Optimized for research and writing
- Modules: RAG, Web Retriever, System Monitor

**Creative**
- Optimized for design work
- Modules: RAG, CLO Companion, Voice Control

**Low-Power**
- CPU-only, minimal resources
- Modules: RAG only, llama.cpp engine

**Switch Profile:**
1. Select profile from dropdown
2. Profile loads automatically
3. Module configuration updates

### Engine Mode

- **Auto:** Automatically selects best engine (recommended)
- **Ollama:** Force Ollama backend
- **llama.cpp:** Force CPU-only llama.cpp

### Theme

- **Dark:** Dark theme (default)
- **Light:** Light theme

Changes apply immediately.

---

## 💾 **Memory & Context**

### What Gets Remembered

The system automatically learns:
- **Preferences:** "prefers_concise", "prefers_detailed", etc.
- **Query patterns:** Frequently asked questions
- **Command usage:** Voice command patterns
- **Session summaries:** Key insights from each session

### Viewing Memory

Memory facts are automatically included in RAG queries. To see what's stored:

```python
from core.memory_manager import get_memory_manager
memory = get_memory_manager()
all_facts = memory.get_all_facts("julian")
print(all_facts)
```

### Context Graph

The context graph combines:
- Your memory/preferences
- Retrieved documents from vault
- System status (CPU, RAM, module health)
- Recent voice commands
- Active CLO projects

This unified context is sent to the LLM with every query for better, personalized answers.

---

## 🐳 **Docker Mode (Advanced)**

### Starting with Docker

1. **Double-click** `launch_docker.bat`
2. **Services start** in background
3. **GUI opens** automatically
4. **All modules** run in containers

### Stopping Docker

- **Double-click** `stop_docker.bat`
- Or: `docker-compose -f docker/docker-compose.yml down`

### Benefits

- Isolated environments
- Easy deployment
- Consistent behavior
- Auto-restart on failure

---

## 🔧 **Troubleshooting**

### GUI Won't Open

**Check:**
- CustomTkinter installed: `pip install customtkinter`
- Python 3.8+ installed
- Check `Logs/` folder for errors

### Voice Control Not Working

**Check:**
- Microphone permissions granted
- `pyaudio` installed: `pip install pyaudio`
- `keyboard` installed: `pip install keyboard`
- Hotkey not conflicting with other apps

### Memory Not Working

**Check:**
- `memory.db` created in project root
- SQLite permissions
- Check logs for database errors

### Context Graph Empty

**Check:**
- Modules registered: `from core.module_registry import get_registry; r = get_registry(); r.register_all()`
- Memory has facts: `memory.context_bundle("julian")`
- System monitor running: `monitor.start()`

---

## 📝 **Daily Usage Tips**

1. **Start with Dashboard** - Check all systems green
2. **Run Full Test** - Verify everything working
3. **Use Voice Commands** - Quick actions without GUI
4. **Check Context Preview** - See what info LLM has access to
5. **Switch Profiles** - Match your current task
6. **Review Memory** - System learns your preferences over time

---

## 🎯 **Success Indicators**

✅ All module status indicators green  
✅ CPU/RAM bars updating smoothly  
✅ Voice commands recognized  
✅ RAG queries return answers with citations  
✅ Context preview shows memory facts  
✅ Preferences persist across sessions  

---

**Happy Researching!** 🚀




