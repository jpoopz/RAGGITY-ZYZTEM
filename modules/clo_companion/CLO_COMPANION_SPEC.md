# CLO Companion Module - Design Specification

**Module ID:** `clo_companion`  
**Version:** 1.0.0  
**Status:** Spec Phase (No implementation yet)  
**Date:** 2025-10-29

---

## 🎯 **Module Purpose**

CLO Companion bridges Llama 3.2 (via Ollama) with CLO3D to enable:
- Natural language → CLO3D design actions
- Design history tracking (undo/redo)
- Design summarization and documentation
- Integration with Academic RAG (shares design context)
- Web Retriever integration (fetches fabric/tech references)

---

## 🔌 **Integration Approach**

### **Option 1: CLO3D Python API/SDK (Preferred, if available)**

**Research Status:** CLO3D does not have a public Python API.  
**Fallback Strategy:** Use one of the options below.

### **Option 2: Python Bridge via Named Pipes/Sockets**

**Approach:**
- CLO3D can execute Python scripts via its scripting interface
- Create a Python server (socket/named pipe on Windows) that CLO Companion connects to
- CLO3D runs a script that sends design state and receives commands
- **Implementation:**
  ```
  CLO Companion ←→ Socket Server ←→ CLO3D Script
  ```

**Pros:**
- Bidirectional communication
- Real-time state updates
- Can query CLO3D state

**Cons:**
- Requires CLO3D to run a script at startup
- More complex setup

### **Option 3: File-Based Communication (Fallback)**

**Approach:**
- CLO Companion writes commands to JSON file in watched directory
- CLO3D script polls file for new commands
- CLO3D writes results/state back to response file
- CLO Companion reads response files

**Pros:**
- Simple, no sockets
- Works across restarts

**Cons:**
- Polling latency
- File locking issues
- No real-time feedback

### **Option 4: UI Automation (Last Resort)**

**Approach:**
- Use `pyautogui` or `pywinauto` to automate CLO3D UI
- Parse natural language → simulate keyboard/mouse actions

**Pros:**
- Works with any CLO3D version

**Cons:**
- Fragile (UI changes break it)
- Limited functionality
- Error-prone

### **RECOMMENDED: Hybrid Approach**

**Phase 1 (Stub):**
- File-based communication (JSON command files)
- CLO Companion writes to `modules/clo_companion/data/commands/`
- CLO3D script (provided separately) reads commands and applies them

**Phase 2 (Future):**
- Add socket server for real-time communication
- Enhanced state querying

---

## 📝 **Command Grammar & Parser**

### **Natural Language Examples**

```
User: "Increase sleeve length by 2cm on jacket_v3"
User: "Change fabric of the skirt to wool"
User: "Add pleats to the front panel"
User: "Tighten the waist by 1.5cm"
User: "Undo the last change"
User: "Export current design to PNG"
```

### **Parser Strategy**

**Step 1: Intent Classification**
- Use Llama 3.2 to classify intent: `modify`, `undo`, `redo`, `render`, `export`, `summarize`

**Step 2: Entity Extraction**
- Extract: garment_name, parameter, value, unit, component (sleeve, waist, etc.)

**Step 3: Command Generation**
- Map to CLO3D action format:
  ```json
  {
    "action": "modify_parameter",
    "garment": "jacket_v3",
    "component": "sleeve",
    "parameter": "length",
    "value": 2.0,
    "unit": "cm",
    "operation": "add"
  }
  ```

### **Grammar Rules**

```
Command := Action [Garment] [Component] [Parameter] [Value] [Unit]

Action := "modify" | "add" | "remove" | "change" | "adjust" | "undo" | "redo" | "render" | "export" | "summarize"

Garment := <filename> | "current" | "active"

Component := "sleeve" | "waist" | "collar" | "front" | "back" | "pocket" | ...

Parameter := "length" | "width" | "fabric" | "drape" | "fit" | ...

Value := <number>
Unit := "cm" | "mm" | "inches" | "percent"
```

---

## 🎨 **Core Actions List**

### **1. Parameter Changes**
- **Modify garment dimensions:** length, width, circumference
- **Adjust fit:** ease, tightness, drape
- **Change materials:** fabric type, color, texture mapping
- **Edit seams:** seam allowance, seam type

### **2. Component Operations**
- **Add components:** pleats, darts, panels, pockets
- **Remove components:** delete seams, remove panels
- **Replace components:** swap fabric, change construction

### **3. Design History**
- **Undo:** Revert last N changes
- **Redo:** Reapply undone changes
- **Version history:** Save snapshots at milestones

### **4. Rendering & Export**
- **Render preview:** Generate PNG/JPG of current state
- **Export garment:** Save .clo file with version number
- **Export snapshot:** Save render + metadata JSON

---

## 🔄 **Undo/Redo Plan**

### **History Stack Structure**

```json
{
  "history": [
    {
      "timestamp": "2025-10-29T18:00:00",
      "action": "modify_parameter",
      "command": "Increase sleeve length by 2cm",
      "garment": "jacket_v3",
      "changes": {
        "parameter": "sleeve_length",
        "old_value": 60.0,
        "new_value": 62.0
      },
      "undo_command": "Decrease sleeve length by 2cm"
    }
  ],
  "current_index": 0
}
```

### **Implementation**
- Store history in `modules/clo_companion/data/history.json`
- Undo: Apply reverse command, move index back
- Redo: Apply forward command, move index forward
- Limit: Max 50 history entries (configurable)

---

## 🖼️ **Render & Export Pipeline**

### **Render Quick Preview**
- **Endpoint:** `POST /render`
- **Action:** Trigger CLO3D render command
- **Output:** PNG/JPG saved to `modules/clo_companion/data/renders/{timestamp}.png`
- **Metadata:** JSON with render settings saved alongside

### **Export Workflow**
1. Save CLO file to versioned folder
2. Generate render preview
3. Save design metadata JSON
4. Optional: Generate markdown summary

**Folder Structure:**
```
modules/clo_companion/data/exports/
├── jacket_v3/
│   ├── v001/ (2025-10-29_18-00-00)
│   │   ├── jacket_v3_v001.clo
│   │   ├── preview.png
│   │   └── metadata.json
│   └── v002/ (2025-10-29_19-00-00)
│       ├── jacket_v3_v002.clo
│       ├── preview.png
│       └── metadata.json
```

---

## 🌐 **API Design**

### **Base URL:** `http://127.0.0.1:5001`

### **Endpoints:**

#### **1. Health Check**
```
GET /health
Response: {
  "status": "healthy" | "degraded" | "unhealthy",
  "module_id": "clo_companion",
  "version": "1.0.0",
  "clo3d_connected": true | false,
  "last_command_time": "2025-10-29T18:00:00"
}
```

#### **2. Apply Design Change**
```
POST /apply_change
Body: {
  "command": "Increase sleeve length by 2cm on jacket_v3",
  "garment": "jacket_v3",  // optional
  "dry_run": false
}
Response: {
  "success": true,
  "command_id": "cmd_12345",
  "parsed_command": {...},
  "changes_applied": {...},
  "preview_url": "/preview/cmd_12345.png"  // if render generated
}
```

#### **3. Undo Last Change**
```
POST /undo
Body: {
  "steps": 1  // optional, default 1
}
Response: {
  "success": true,
  "undone_command": {...},
  "current_state": {...}
}
```

#### **4. Redo Last Undone Change**
```
POST /redo
Body: {
  "steps": 1
}
Response: {
  "success": true,
  "redone_command": {...}
}
```

#### **5. Render Preview**
```
POST /render
Body: {
  "garment": "jacket_v3",
  "quality": "high" | "medium" | "low",
  "view_angle": "front" | "back" | "side" | "3d"
}
Response: {
  "success": true,
  "render_path": "data/renders/2025-10-29_18-00-00.png",
  "render_url": "/render/2025-10-29_18-00-00.png"
}
```

#### **6. Export Design**
```
POST /export
Body: {
  "garment": "jacket_v3",
  "include_render": true,
  "include_metadata": true,
  "version_comment": "First iteration"
}
Response: {
  "success": true,
  "export_path": "data/exports/jacket_v3/v001/",
  "files": ["jacket_v3_v001.clo", "preview.png", "metadata.json"]
}
```

#### **7. Summarize Design**
```
POST /summarize_design
Body: {
  "garment": "jacket_v3",
  "include_history": true,
  "format": "markdown" | "json"
}
Response: {
  "summary": "Design summary text...",
  "specifications": {...},
  "history": [...],
  "render_url": "/render/..."
}
```

---

## 📋 **Message Schema**

### **Command Message (CLO Companion → CLO3D)**

```json
{
  "id": "cmd_12345",
  "timestamp": "2025-10-29T18:00:00",
  "action": "modify_parameter",
  "garment": "jacket_v3.clo",
  "component": "sleeve",
  "parameter": "length",
  "value": 62.0,
  "unit": "cm",
  "operation": "add",
  "dry_run": false
}
```

### **Response Message (CLO3D → CLO Companion)**

```json
{
  "id": "cmd_12345",
  "timestamp": "2025-10-29T18:00:01",
  "success": true,
  "changes_applied": {
    "parameter": "sleeve_length",
    "old_value": 60.0,
    "new_value": 62.0
  },
  "preview_path": "renders/2025-10-29_18-00-01.png",
  "error": null
}
```

---

## 🔗 **Interoperability**

### **Academic RAG Integration**

**Flow:**
1. User asks RAG: "How should I modify this dress for sustainability?"
2. RAG retrieves academic context (sustainable fashion guidelines)
3. RAG publishes event: `design_query_received` with query + context
4. CLO Companion receives event
5. CLO Companion generates design suggestions using Llama 3.2
6. CLO Companion applies changes (or suggests changes)
7. CLO Companion publishes `design_modification_applied` event
8. RAG includes CLO actions in response

**Data Sharing:**
- CLO Companion writes design summaries to `shared/data/design_context.json`
- Academic RAG reads design context for citation in responses
- Markdown summary saved to Obsidian vault (via Academic RAG's writer)

### **Web Retriever Integration**

**Flow:**
1. User asks CLO Companion: "What's the best fabric for this design?"
2. CLO Companion queries Web Retriever: `/summarize_web?query=fabric+recommendations+for+jacket`
3. Web Retriever fetches web results and summarizes
4. CLO Companion uses summary to suggest fabric changes
5. Web Retriever saves research to Obsidian vault

---

## ⚡ **Performance & Safety**

### **Rate Limiting**
- **Max commands per minute:** 10 (configurable)
- **Max concurrent renders:** 2 (to prevent CLO3D overload)
- **Command queue:** If rate limit exceeded, queue commands

### **Dry-Run Mode**
- **Enable via:** `POST /apply_change {"dry_run": true}`
- **Behavior:** Parse command, validate, return proposed changes WITHOUT applying
- **Use case:** Preview changes before applying

### **Error Handling**
- **CLO3D disconnected:** Return 503 with message "CLO3D not connected"
- **Invalid command:** Return 400 with parsed error details
- **CLO3D error:** Capture error from CLO3D script, return 500

### **State Verification**
- Before applying change, query CLO3D current state
- After change, verify state changed correctly
- If mismatch, log warning and offer undo

---

## 📁 **Module Structure**

```
modules/clo_companion/
├── __init__.py
├── module_info.json
├── api.py                    # Flask server
├── command_parser.py         # NLP → CLO command mapping
├── clo_interface.py          # CLO3D communication layer
├── design_history.py         # Undo/redo management
├── render_export.py          # Render and export pipeline
├── data/
│   ├── commands/             # Command files (file-based comm)
│   ├── responses/            # Response files
│   ├── history.json          # Design history stack
│   ├── renders/              # Render outputs
│   └── exports/              # Versioned exports
├── config.json               # Module configuration
└── README.md
```

---

## 🛠️ **Configuration Schema**

```json
{
  "module_id": "clo_companion",
  "api": {
    "host": "127.0.0.1",
    "port": 5001,
    "cors_enabled": false
  },
  "clo3d": {
    "connection_method": "file",  // "file" | "socket" | "ui_automation"
    "command_dir": "data/commands",
    "response_dir": "data/responses",
    "poll_interval_seconds": 1.0
  },
  "rate_limiting": {
    "max_commands_per_minute": 10,
    "max_concurrent_renders": 2
  },
  "history": {
    "max_entries": 50,
    "auto_save": true
  },
  "rendering": {
    "default_quality": "medium",
    "auto_render_after_change": false
  },
  "export": {
    "base_path": "data/exports",
    "version_format": "v{num:03d}",
    "include_render": true,
    "include_metadata": true
  }
}
```

---

## ✅ **Phase 1 Implementation Scope**

**Stub Implementation:**
- ✅ `module_info.json` with all metadata
- ✅ Flask server with `/health` endpoint
- ✅ Stub endpoints: `/apply_change`, `/undo`, `/redo`, `/render`, `/export`, `/summarize_design`
- ✅ All endpoints return polite JSON: `{"status": "stub", "message": "CLO Companion not yet implemented"}`
- ✅ Settings UI in GUI for configuring connection method and paths

**Full Implementation (Phase 2):**
- Implement command parser (Llama 3.2-based)
- File-based communication with CLO3D
- Design history management
- Render pipeline
- Export pipeline
- Academic RAG interop
- Web Retriever interop

---

## 📝 **Security Notes**

- **Localhost-only:** All endpoints bind to 127.0.0.1
- **AUTH_TOKEN:** Required for inter-module calls
- **Command validation:** Sanitize all user inputs before sending to CLO3D
- **File path security:** Prevent directory traversal in command/export paths

---

## 🎯 **Success Criteria**

1. **Natural language parsing:** 90%+ accuracy on standard design commands
2. **CLO3D integration:** Reliable command delivery and response
3. **Undo/redo:** 100% accuracy (no state drift)
4. **Performance:** <5s for parameter changes, <30s for renders
5. **Interop:** Seamless Academic RAG and Web Retriever integration

---

**Status:** ✅ **Spec Complete - Ready for Review**

*This spec defines the CLO Companion module architecture. No code implementation until spec is approved and Phase 1 stub requirements are met.*




