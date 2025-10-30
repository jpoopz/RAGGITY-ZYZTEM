# CLO Companion - Prompt Router Guide

**Version:** 5.0.0-Julian-AdaptiveModes  
**Last Updated:** 2025-10-29

---

## 🎯 **OVERVIEW**

The CLO Companion now uses **adaptive dual-prompt logic** that automatically switches between two specialized modes:

- **CHAT Mode** - Open conversation, brainstorming, research
- **CLO_WIZARD Mode** - Structured JSON commands for garment modification

The system intelligently detects when to switch modes based on user input and automatically returns to CHAT after command execution.

---

## 🔄 **MODES EXPLAINED**

### **CHAT Mode (Green Indicator)**

**Purpose:** Creative conversation and ideation

**Behavior:**
- Natural language responses
- Brainstorms design ideas
- Combines academic reasoning
- Suggests CLO_WIZARD when actionable feedback is detected
- No structured output required

**System Prompt:**
```
You are Julian's creative design and research assistant.
Engage in open conversation, brainstorm garment ideas, 
combine academic reasoning, and respond naturally.
```

**Triggers CHAT Mode:**
- Questions: "What fabrics are trending?"
- Research: "Tell me about minimal hoodies"
- Brainstorming: "Let's design a minimal hoodie"
- Conversational queries

---

### **CLO_WIZARD Mode (Blue Glow Indicator)**

**Purpose:** Structured command execution

**Behavior:**
- Outputs ONLY JSON commands
- No natural language in response
- Limited token output (max 200)
- Auto-reverts to CHAT after execution

**System Prompt:**
```
You are CLO WIZARD — a procedural garment-generation AI 
controlling Python tools: garment_gen.py, garment_editor.py, 
and preview_manager. Respond **only** in structured JSON commands.
```

**Triggers CLO_WIZARD Mode:**
- Actionable commands: "make sleeves longer"
- Adjustments: "change color to black"
- Modifications: "make it fitted"
- Edit requests: "shorten the hem"

---

## 🧠 **HOW MODE DETECTION WORKS**

### **Detection Logic**

The `prompt_router.route_prompt()` function analyzes user input using regex patterns:

**CLO_WIZARD Triggers:**
```
- "make sleeve/sleeves"
- "adjust (sleeve|hem|length|width|fit)"
- "change (color|material|fabric)"
- "shorten|longer|wider|narrower"
- "make it (fitted|oversized)"
- "add/remove (logo|belt|hood)"
- "undo|revert|edit|modify"
```

**CHAT Triggers (when in CLO_WIZARD):**
```
- Questions: "what|how|why|when|where"
- Explanatory: "explain|describe|tell me"
- Research: "trend|research|academic"
- Ideation: "idea|brainstorm|suggest"
```

### **Example Flow**

```
User: "Let's design a minimal hoodie"
→ Detected: CHAT mode (brainstorming)
→ Response: Natural conversation about hoodie styles

User: "Make the sleeves longer"
→ Detected: CLO_WIZARD mode (actionable command)
→ Response: JSON commands → Garment edited → Auto-return to CHAT

User: "What fabrics are trending?"
→ Detected: CHAT mode (question)
→ Response: Natural language research answer
```

---

## 📊 **CONTEXT ASSEMBLY**

### **Context Components**

When building context for LLM calls, the system combines:

1. **System Prompt** (mode-specific)
   - CHAT: Conversational assistant prompt
   - CLO_WIZARD: Structured JSON command prompt

2. **Design Context** (from `design_state.json`)
   - Current file: `garment_xxx_v2.obj`
   - Version: `2`
   - Attributes: `color: black, fabric: cotton, fit: oversized`
   - Original prompt: `"white cotton t-shirt"`

3. **Recent Conversation** (last 6 messages)
   - Keeps context tight for performance
   - Format: `role: message`

### **Example Context**

```
[System Prompt]
Current Design:
File: garment_20251029_143022_shirt_5678_v2.obj (v2)
Attributes: color: black, material: cotton, fit: oversized
Original prompt: white cotton t-shirt with rolled sleeves

Recent Conversation:
user: make sleeves longer
ai: ✅ Updated to v2: garment_xxx_v2.obj
user: change color to navy
```

---

## 🛠️ **TOOLS & FUNCTIONS**

### **CLO_WIZARD Tools**

When in CLO_WIZARD mode, the following tools are attached:

```json
{
  "garment_gen": {
    "description": "Generate new garment from prompt",
    "function": "generate_garment",
    "params": ["prompt", "seed"]
  },
  "garment_editor": {
    "description": "Edit existing garment OBJ file",
    "function": "apply_edit",
    "params": ["model_path", "edit_commands"]
  },
  "preview_manager": {
    "description": "Generate preview images",
    "function": "generate_preview",
    "params": ["obj_file", "output_path"]
  },
  "design_state": {
    "description": "Query current design state",
    "function": "get_current_state",
    "params": []
  }
}
```

**CHAT Mode:** No tools attached (conversational only)

---

## 🎨 **GUI INDICATORS**

### **Mode Display**

In the CLO Companion Chat tab:

1. **Color Bar**
   - 🟢 **Green:** CHAT Mode
   - 🔵 **Blue Glow:** CLO_WIZARD Active

2. **Mode Label**
   - "CHAT Mode" (green)
   - "CLO_WIZARD Active" (blue)

3. **Prompt Excerpt**
   - CHAT: "Mode: Creative conversation assistant"
   - CLO_WIZARD: "Mode: Structured JSON command execution"

4. **Live Updates**
   - Mode switches update in real-time
   - Console shows: `[MODE] Entered CLO_WIZARD`
   - After edit: `[MODE] Returned to CHAT`

---

## 📝 **LLM INVOCATION CHANGES**

### **Token Limits**

- **CHAT Mode:** Default (500 tokens)
- **CLO_WIZARD Mode:** Limited (200 tokens) for focused JSON output

### **Temperature Settings**

- **CHAT Mode:** 0.3 (balanced creativity)
- **CLO_WIZARD Mode:** 0.2 (more deterministic for JSON)

### **JSON Parsing**

1. Attempt to extract JSON from response
2. Validate structure
3. If CLO_WIZARD mode and invalid JSON:
   - Auto-retry with constraint reminder
   - "Remember: You must output ONLY valid JSON"
4. Fallback to keyword parsing if retry fails

---

## 🔄 **MODE TRANSITIONS**

### **Automatic Switching**

1. **CHAT → CLO_WIZARD**
   - Trigger: Actionable design command detected
   - Action: Load CLO_WIZARD prompt, attach tools
   - Log: `[MODE] Entered CLO_WIZARD`

2. **CLO_WIZARD → CHAT**
   - Trigger: Command execution completed OR conversational query
   - Action: Load CHAT prompt, remove tools
   - Log: `[MODE] Returned to CHAT`

### **Manual Override**

Currently automatic, but future versions may include:
- Manual mode toggle button
- Mode preference settings
- Persistent mode for multi-step workflows

---

## 📊 **LOGGING**

### **Log Files**

1. **Logs/clo_prompt_router.log**
   - Mode switches
   - Prompt selections
   - Context truncations
   - Retry attempts

**Example Entries:**
```
[2025-10-29T14:30:05] [mode_switch] CHAT → CLO_WIZARD | Input: make sleeves longer
[2025-10-29T14:30:10] [context_built] mode=CLO_WIZARD, parts=2
[2025-10-29T14:30:15] [tools_attached] CLO_WIZARD (4 tools)
[2025-10-29T14:30:20] [mode_set] CLO_WIZARD → CHAT
```

2. **Standard Logs**
   - `[MODE]` category entries in main log
   - Shows mode transitions in real-time

---

## 🧪 **TEST SCENARIOS**

### **Scenario 1: Design Session**

```
1. Launch Control Panel → CLO tab → Chat & Iterate

2. User: "Let's design a minimal hoodie"
   → Mode: CHAT
   → Response: Natural conversation about hoodie styles
   → Indicator: Green

3. User: "Make the sleeves longer"
   → Mode: Auto-switches → CLO_WIZARD
   → Response: JSON commands → Edit executed
   → Indicator: Blue → Green (auto-return)

4. User: "What fabrics are trending?"
   → Mode: CHAT (stays in CHAT)
   → Response: Research/trending info
   → Indicator: Green
```

### **Scenario 2: Multi-Step Edit**

```
1. User: "make it fitted"
   → Mode: CLO_WIZARD
   → Edit: Fit adjustment
   → Auto-return to CHAT

2. User: "change color to navy"
   → Mode: CLO_WIZARD
   → Edit: Color change
   → Auto-return to CHAT

3. User: "undo last change"
   → Mode: CLO_WIZARD
   → Action: Revert
   → Auto-return to CHAT
```

---

## ⚙️ **CONFIGURATION**

### **Mode Detection Sensitivity**

Adjust regex patterns in `prompt_router.py`:

```python
wizard_triggers = [
    r"make (sleeve|sleeves)",  # Add more patterns here
    r"adjust (sleeve|hem|length|width|fit)",
    # ...
]
```

### **Context Size**

Modify `build_context()` to change:
- Chat history limit (default: 6 messages)
- Design context fields (essential keys only)

### **Token Limits**

Adjust in `feedback_interpreter.py`:

```python
if mode == "CLO_WIZARD":
    max_tokens = 200  # Change limit here
```

---

## 🔍 **TROUBLESHOOTING**

### **Mode Not Switching**

**Symptoms:** Always in CHAT when commands given

**Solutions:**
- Check `Logs/clo_prompt_router.log` for detection events
- Verify regex patterns match your input style
- Try rephrasing: "make sleeves longer" vs "lengthen sleeves"

### **Invalid JSON in CLO_WIZARD**

**Symptoms:** JSON parse errors

**Solutions:**
- System auto-retries with constraint reminder
- Check temperature setting (should be 0.2 for CLO_WIZARD)
- Verify Ollama model supports structured output

### **Mode Stuck in CLO_WIZARD**

**Symptoms:** Doesn't return to CHAT after edit

**Solutions:**
- Check logs for "Auto-return" messages
- Verify edit execution completed successfully
- Manual refresh: Click "Refresh Mode" button

### **Context Too Long**

**Symptoms:** Slow responses, high token usage

**Solutions:**
- Reduce chat history limit (default: 6)
- Trim design context fields
- Check `context_built` log entries

---

## 📚 **API ENDPOINTS**

### **Mode Management**

No direct mode endpoints (handled internally), but mode affects:

- `/iterate` - Uses current mode for prompt selection
- `/design_state` - Provides context for mode detection
- `/chat_history` - Provides conversation history for context

---

## ✅ **SUCCESS CRITERIA**

After implementing Phase 5:

- ✅ Automatic mode switching based on input
- ✅ Distinct GUI indicators (Green/Blue)
- ✅ Structured JSON in CLO_WIZARD mode
- ✅ Natural language in CHAT mode
- ✅ Auto-return to CHAT after edits
- ✅ Logs show all mode transitions
- ✅ Context assembly uses last 6 messages
- ✅ Design state provides essential context
- ✅ Token limits enforced per mode
- ✅ JSON retry logic functional

---

## 🎯 **FUTURE ENHANCEMENTS**

Planned improvements:

1. **Persistent Wizard Mode**
   - Option to stay in CLO_WIZARD for multi-step workflows
   - "Keep in Wizard Mode" toggle

2. **Custom Triggers**
   - User-defined regex patterns
   - Configurable mode preferences

3. **Mode Confidence Scores**
   - Show detection confidence in GUI
   - Allow manual override if uncertain

4. **Context Preview**
   - Show assembled context before LLM call
   - Edit context manually if needed

---

**Happy Designing with Adaptive Modes! 💬🔧**

*CLO Companion v5.0.0-Julian-AdaptiveModes*




