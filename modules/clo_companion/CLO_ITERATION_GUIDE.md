# CLO Companion - Iterative Design Guide

**Version:** 4.3.0-Julian-IterativeDesign  
**Last Updated:** 2025-10-29

---

## 🎯 **OVERVIEW**

CLO Companion now supports **conversational iteration** - you can chat with the system to refine existing garments instead of regenerating from scratch. Each iteration creates a new version (v1, v2, v3...) while preserving the design history.

---

## 💬 **HOW IT WORKS**

### **Workflow**

1. **Generate Initial Design**
   - Use "⚙️ Generate" tab → create a garment (e.g., "white cotton t-shirt")

2. **Switch to Chat Tab**
   - Click "💬 Chat & Iterate" tab
   - The system remembers your current design

3. **Give Feedback**
   - Type natural language: "make sleeves longer"
   - Or: "change color to black"
   - Or: "make it more fitted"

4. **Iteration Happens**
   - System interprets your feedback
   - Modifies the existing OBJ file
   - Creates new version: `garment_xxx_v2.obj`
   - Updates preview and chat history

5. **Continue Iterating**
   - Give more feedback on the updated design
   - Each change increments the version number

---

## 📝 **FEEDBACK EXAMPLES**

### **Iteration Requests (Modifies Existing)**

These modify the current design:

```
make sleeves longer
make it shorter
change color to black
make it more fitted
make it oversized
shorten the hem
adjust the width
make sleeves shorter
change material to leather
add a belt
```

### **New Generation Requests (Creates New)**

These trigger a completely new generation:

```
make a denim jacket
create a black dress
generate a wool sweater
i want a red coat
```

**How it's detected:** The system checks if your feedback starts with "make a", "create a", "generate a", "new", etc.

---

## 🔧 **TECHNICAL DETAILS**

### **Design State Tracking**

The system maintains `modules/clo_companion/context/design_state.json`:

```json
{
  "current_file": "garment_20251029_143022_shirt_5678_v2.obj",
  "history": ["garment_xxx_v1.obj", "garment_xxx_v2.obj"],
  "attributes": {
    "garment_type": "shirt",
    "material": "cotton",
    "sleeve_length": "short"
  },
  "last_prompt": "white cotton t-shirt with rolled sleeves",
  "version": 2,
  "last_update": "2025-10-29T14:35:00"
}
```

### **Chat History**

Stored in `modules/clo_companion/context/clo_chat_history.json`:

```json
[
  {
    "role": "user",
    "message": "make sleeves longer",
    "timestamp": "2025-10-29T14:30:00"
  },
  {
    "role": "ai",
    "message": "✅ Updated to v2: garment_xxx_v2.obj",
    "timestamp": "2025-10-29T14:30:05"
  }
]
```

### **Change Log**

All iterations are logged to `Logs/clo_changes.log`:

```
[2025-10-29T14:30:05] [ITERATE] garment_xxx_v1.obj → garment_xxx_v2.obj | Feedback: make sleeves longer | Commands: [{"action":"adjust_sleeve_length","value":"+2.5","unit":"cm"}]
```

---

## 🎛️ **GUI FEATURES**

### **Chat Panel**

1. **Chat History Area**
   - Scrollable view of conversation
   - Shows timestamps
   - User messages: `[HH:MM] You: ...`
   - AI responses: `[HH:MM] CLO: ✅ ...`

2. **Input Box**
   - Multi-line text input
   - Press Enter to send (Shift+Enter for newline)
   - Placeholder: "Type feedback or new idea..."

3. **Buttons**
   - **💬 Send Feedback** - Send your message
   - **↶ Undo** - Revert to previous version
   - **Clear Chat** - Clear chat history (GUI only)

4. **Status Label**
   - Shows current status: "Ready for feedback", "Processing...", "✅ Ready"

### **Version Display**

- Generated garments show version in outputs list
- Format: `garment_xxx_v2.obj`
- Undo button reverts to previous version

---

## 🔄 **ITERATION PROCESS**

### **1. Feedback Interpretation**

The system uses **Llama 3.2** (via Ollama) to parse your feedback:

```
User: "make sleeves longer"
↓
LLM Analysis:
{
  "action": "adjust_sleeve_length",
  "value": "+2.5cm",
  "commands": [
    {"action": "adjust_sleeve_length", "value": "+2.5", "unit": "cm"}
  ],
  "confidence": 0.95,
  "is_new_generation": false
}
```

### **2. OBJ Editing**

The `garment_editor.py` module:

1. Loads the current OBJ file (using trimesh)
2. Identifies regions (sleeves, hem, body, etc.)
3. Applies transformations based on commands
4. Saves new version with `_v2.obj`, `_v3.obj`, etc.

### **3. Material Updates**

Color and material changes update the `.mtl` file:

- "change color to black" → updates Kd in MTL
- "change material to leather" → updates material properties

---

## 📊 **SUPPORTED ACTIONS**

The feedback interpreter recognizes:

| Action | Example Feedback | Effect |
|--------|-----------------|--------|
| `adjust_sleeve_length` | "make sleeves longer" | Extends/contracts sleeve vertices |
| `adjust_hem_length` | "shorten the hem" | Adjusts bottom edge |
| `adjust_width` | "make it wider" | Scales X-axis |
| `adjust_length` | "make it longer" | Scales Y-axis |
| `change_color` | "change to black" | Updates material color |
| `change_material` | "make it denim" | Changes material properties |
| `adjust_fit` | "make it fitted" | Overall scale adjustment |
| `add_belt` | "add a belt" | Adds belt geometry (if supported) |

---

## 🔙 **UNDO FEATURE**

### **How to Undo**

1. Click **↶ Undo** button in chat panel
2. System reverts to previous version
3. State updates to previous file
4. Chat shows: `✅ Reverted to: garment_xxx_v1.obj`

### **Limitations**

- Only works if there's a previous version in history
- Cannot undo beyond the first version (v1)
- Undo affects the current design state, not file deletion

---

## 📁 **FILE STRUCTURE**

After iterations, your `outputs/` folder contains:

```
modules/clo_companion/outputs/
├── garment_20251029_143022_shirt_5678.obj          (v1)
├── garment_20251029_143022_shirt_5678.mtl
├── garment_20251029_143022_shirt_5678_metadata.json
├── garment_20251029_143022_shirt_5678_v2.obj       (v2)
├── garment_20251029_143022_shirt_5678_v2.mtl
├── garment_20251029_143022_shirt_5678_v2_metadata.json
└── previews/
    ├── garment_xxx_preview.png
    └── garment_xxx_v2_preview.png
```

---

## ⚠️ **ERROR HANDLING**

### **If Iteration Fails**

1. **Fallback to Regeneration**
   - If OBJ editing fails, system regenerates from scratch
   - Uses feedback as new prompt
   - Logs error: `[CLO][ERROR] Failed to apply feedback: {error}`

2. **Common Issues**
   - **trimesh not available:** Install with `pip install trimesh`
   - **Ollama not running:** Start Ollama service for feedback interpretation
   - **File not found:** Ensure current design exists before iterating

3. **Error Messages**
   - Chat displays: `❌ Error: {message}`
   - Check `Logs/clo_changes.log` for details

---

## 🧪 **TESTING WORKFLOW**

### **Recommended Test Sequence**

1. ✅ Generate: "box logo t-shirt"
   - Verify: `garment_xxx.obj` created (v1)

2. ✅ Iterate: "make sleeves longer"
   - Verify: `garment_xxx_v2.obj` created
   - Check chat shows: `✅ Updated to v2`
   - Preview updated

3. ✅ Iterate: "change color to black"
   - Verify: `garment_xxx_v3.obj` created
   - MTL file updated
   - Chat shows version increment

4. ✅ Undo: Click "↶ Undo"
   - Verify: State reverts to v2
   - Chat shows revert message

5. ✅ New Generation: "make a denim jacket"
   - Verify: New garment created (starts at v1 again)
   - Old design preserved in outputs folder

---

## 📚 **API ENDPOINTS**

### **Iterate Endpoint**

```bash
POST http://127.0.0.1:5001/iterate
Content-Type: application/json

{
  "feedback": "make sleeves longer"
}
```

**Response:**
```json
{
  "status": "success",
  "obj_file": "garment_xxx_v2.obj",
  "version": 2,
  "message": "Design updated to v2"
}
```

### **Chat History**

```bash
GET http://127.0.0.1:5001/chat_history?limit=50
```

### **Design State**

```bash
GET http://127.0.0.1:5001/design_state
```

### **Undo**

```bash
POST http://127.0.0.1:5001/undo
```

---

## 🔗 **INTEGRATION NOTES**

### **Event Bus**

Iterations publish events:
- `clo.design_iterated` - When iteration completes

### **Memory Integration**

Design iterations are logged in memory manager:
- Category: `clo_projects`
- Includes version history and feedback

### **Cloud Bridge**

Iteration state can be synced to VPS:
- `design_state.json` synced automatically
- Chat history synced if enabled

---

## 💡 **BEST PRACTICES**

1. **Be Specific**
   - ❌ "make it better"
   - ✅ "make sleeves 2cm longer"

2. **One Change at a Time**
   - Easier to track what each iteration did
   - Version history stays clear

3. **Use Undo for Quick Reverts**
   - Don't need to regenerate if one change was wrong
   - Can continue from previous version

4. **Check Preview After Each Iteration**
   - Verify changes look correct
   - Preview updates automatically

5. **Review Change Log**
   - `Logs/clo_changes.log` shows full history
   - Useful for debugging or understanding changes

---

## ✅ **SUCCESS CRITERIA**

After following this guide:

- ✅ Can generate initial garment
- ✅ Can iterate with natural language feedback
- ✅ New versions created (v2, v3, etc.)
- ✅ Chat history preserved
- ✅ Undo works correctly
- ✅ Files stored in `outputs/` folder
- ✅ Change log records all iterations

---

**Happy Iterating! 💬👗**

*CLO Companion v4.3.0-Julian-IterativeDesign*




