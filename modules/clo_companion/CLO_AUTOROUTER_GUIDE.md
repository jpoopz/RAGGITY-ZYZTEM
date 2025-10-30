# CLO Companion - AutoRouter Guide

**Version:** 6.0.0-Julian-HybridChat  
**Last Updated:** 2025-10-29

---

## 🎯 **OVERVIEW**

The CLO Companion now features **automatic per-message routing** between CHAT and EDIT modes. Users interact through one continuous chat interface, and the system automatically detects when to execute garment modifications.

**Key Concept:** No manual mode switching required. The system intelligently routes each message based on intent.

---

## 🔄 **HOW ROUTING WORKS**

### **Intent Detection Process**

For every message, the system:

1. **Keyword Check** → Fast pattern matching
2. **Strong Pattern Check** → High-confidence triggers
3. **CHAT Indicator Override** → Conversational queries
4. **LLM Classification** → Ambiguous cases (if Ollama available)

**Decision Threshold:** Confidence > 0.6 = EDIT intent

### **Example Flow**

```
User: "Let's design a hoodie"
→ Intent: CHAT (confidence: 0.9, method: chat_indicator)
→ Mode: CHAT
→ Response: Natural conversation about hoodie styles

User: "Make the logo smaller"
→ Intent: EDIT (confidence: 0.95, method: strong_pattern)
→ Mode: CLO_WIZARD (auto-activated)
→ Action: Executes garment_editor.modify_logo
→ Response: "✅ Updated to v2 — preview updated."
→ Auto-return: Back to CHAT mode

User: "Now explain fabric blends"
→ Intent: CHAT (confidence: 0.9, method: chat_indicator)
→ Mode: CHAT
→ Response: Informative text about fabric blends
```

---

## 🧠 **INTENT CLASSIFICATION LOGIC**

### **EDIT Intent Keywords**

The system recognizes these keywords as EDIT intent:

```python
["make", "add", "change", "remove", "shorten", "lengthen",
 "color", "logo", "fabric", "resize", "replace", "adjust",
 "modify", "edit", "update", "set", "increase", "decrease",
 "expand", "shrink", "widen", "narrow", "tighter", "looser",
 "fitted", "oversized", "longer", "shorter", "bigger", "smaller",
 "undo", "revert", "cuff", "sleeve", "hem", "collar", "belt",
 "hood", "pocket"]
```

### **Strong EDIT Patterns** (High Confidence: 0.95)

Patterns that always trigger EDIT:

```regex
"make (sleeve|sleeves|logo|hem|fit|it)"
"adjust (sleeve|color|logo|fit|length|width)"
"change (color|colour|logo|fit|length|width)"
"add/remove (logo|belt|hood|cuff|collar|pocket)"
"shorten/lengthen/widen/narrow (sleeve|hem|collar)"
"make it (fitted|oversized|tighter|looser)"
"resize (logo|sleeve)"
"undo|revert"
"v\d+|version \d+"
```

### **CHAT Indicators** (Override to CHAT)

These patterns force CHAT mode:

```regex
"what|how|why|when|where"
"explain|describe|tell me|inform"
"trend|trending|research|academic"
"idea|brainstorm|suggest|recommend"
"think|opinion|thought|believe"
"discuss|talk about|share"
```

### **LLM Classification** (Fallback)

For ambiguous cases:

- Uses local Llama 3.2
- Prompt: "Decide if this message is a garment edit command (yes/no): {text}"
- Temperature: 0.1 (very deterministic)
- Token limit: 5 (just yes/no)

---

## 📊 **ROUTING BEHAVIOR**

### **When EDIT Intent Detected**

1. **Mode Switch**
   - Automatically switches to CLO_WIZARD mode
   - Loads CLO_WIZARD_PROMPT (single-turn execution)
   - Logs: `[MODE:EDIT]` in autorouter.log

2. **Execution**
   - Runs `garment_editor` or `garment_gen` command
   - Applies modifications
   - Auto-saves version
   - Generates preview

3. **Response**
   - Returns summary: `"✅ {edit_summary} — preview updated."`
   - Auto-saved to design_state.json
   - Preview regenerated

4. **Auto-Return**
   - Automatically reverts to CHAT prompt
   - Ready for next message
   - No manual mode switching needed

### **When CHAT Intent Detected**

1. **Mode Stay**
   - Remains in CHAT mode
   - Loads CHAT_PROMPT
   - Logs: `[MODE:CHAT]` in autorouter.log

2. **Response**
   - Natural language conversational response
   - No garment modifications executed
   - Chat history updated

---

## 🎨 **GUI ENHANCEMENTS**

### **Visual Feedback**

1. **Transient Overlay**
   - Shows "🪄 CLO Wizard Active" when EDIT detected
   - Appears at top of chat panel
   - Fades after 1.5 seconds
   - Blue background (#2196F3)

2. **Message Prefixes**
   - `[CHAT]` prefix (gray) for conversational messages
   - `[EDIT]` prefix (blue) for edit commands

3. **Status Bar Updates**
   - "Auto → CLO_WIZARD mode" when EDIT detected
   - "Auto → Chat mode" for conversational messages

### **Removed Manual Controls**

- Mode toggle buttons removed (now automatic)
- "Refresh Mode" button kept for debugging
- Seamless single-chat experience

---

## 📝 **LOGGING & METRICS**

### **Log File: `Logs/clo_autorouter.log`**

**Format:**
```
[Timestamp] [MODE:CHAT/EDIT] [TextExcerpt] [Confidence:0.XX] [Method:pattern|llm]
```

**Example Entries:**
```
[2025-10-29T14:30:05] [MODE:EDIT] [make sleeves longer] [Confidence:0.95] [Method:strong_pattern]
[2025-10-29T14:30:10] [MODE:CHAT] [what fabrics are trending] [Confidence:0.90] [Method:chat_indicator]
[2025-10-29T14:30:15] [MODE:EDIT] [change color to navy] [Confidence:0.85] [Method:keyword_match_2]
[2025-10-29T14:30:20] [FALSE_POSITIVE] Detected:EDIT Correct:CHAT Text:make me understand
```

### **Diagnostics Integration**

Health check now includes:

- ✅ **AutoRouter Operational** - Verifies intent detection working
- ✅ **AutoRouter Statistics** - Counts EDIT vs CHAT turns
- ✅ **Average Confidence** - Calculated from recent decisions

**Example Output:**
```
✅ AutoRouter Operational: Intent detection working (conf: 0.95)
✅ AutoRouter Statistics: EDIT: 12, CHAT: 45, Total: 57
```

---

## 🔧 **USER FEEDBACK LOOP**

### **Reporting False Positives**

If the system incorrectly routes a message:

1. Type `/wrong` after the incorrect response
2. System records false positive in autorouter.log
3. Format: `[FALSE_POSITIVE] Detected:{intent} Correct:{intent} Text:{message}`
4. Future fine-tuning can use this data

**Example:**
```
User: "make me understand fabric blends"
→ System detects: EDIT (wrong!)
→ User types: "/wrong"
→ System records: [FALSE_POSITIVE] Detected:EDIT Correct:CHAT
```

---

## ⚙️ **CONFIGURATION**

### **Adding Custom Keywords**

Edit `intent_classifier.py`:

```python
# In IntentClassifier.__init__():
self.edit_keywords.append("your_keyword")
```

Or use API:

```python
classifier = get_intent_classifier()
classifier.add_edit_keyword("custom_action")
```

### **Adjusting Confidence Threshold**

In `intent_classifier.py`, modify:

```python
if llm_confidence > 0.6:  # Change threshold here
    return (llm_intent, llm_confidence)
```

### **Disabling LLM Classification**

If Ollama unavailable, system falls back to keyword-only:

```python
# In detect_intent():
if ollama:  # Remove this check to disable LLM
    llm_intent, llm_confidence = self._llm_classify(text)
```

---

## 🧪 **TESTING SCENARIOS**

### **Test 1: Conversational Query**

**Input:** "Let's design a hoodie."

**Expected:**
- Intent: CHAT
- Confidence: 0.9
- Method: chat_indicator
- Response: Natural conversation about hoodie styles
- Prefix: `[CHAT]`

---

### **Test 2: Edit Command**

**Input:** "Make the logo smaller."

**Expected:**
- Intent: EDIT
- Confidence: 0.95
- Method: strong_pattern
- Mode: Auto-switches to CLO_WIZARD
- Action: Executes `garment_editor.modify_logo(size=-20%)`
- Response: "✅ Updated to v2 — preview updated."
- Prefix: `[EDIT]`
- Overlay: Shows "🪄 CLO Wizard Active" (1.5s)
- Auto-return: Back to CHAT

---

### **Test 3: Explanatory Query**

**Input:** "Now explain fabric blends."

**Expected:**
- Intent: CHAT
- Confidence: 0.9
- Method: chat_indicator
- Response: Informative text about fabric blends
- Prefix: `[CHAT]`

---

### **Test 4: Complex Edit**

**Input:** "Add cuffs to the sleeves."

**Expected:**
- Intent: EDIT
- Confidence: 0.85
- Method: keyword_match_2
- Mode: Auto-switches to CLO_WIZARD
- Action: Executes `garment_editor.add_cuffs()`
- Response: "✅ Updated to v3 — preview updated."
- Logs: Change logged to `clo_changes.log`

---

## 🔍 **DEBUGGING**

### **Check Intent Detection**

View autorouter log:

```bash
tail -f Logs/clo_autorouter.log
```

### **Test Intent Classifier Directly**

```python
from modules.clo_companion.intent_classifier import get_intent_classifier

classifier = get_intent_classifier()
intent, confidence = classifier.detect_intent("make sleeves longer")
print(f"Intent: {intent}, Confidence: {confidence}")
```

### **Common Issues**

**Issue:** All messages routed to CHAT

**Solutions:**
- Check if keywords match user input style
- Verify regex patterns in `strong_edit_patterns`
- Test with explicit edit command: "make sleeves longer"

---

**Issue:** False positives (EDIT when should be CHAT)

**Solutions:**
- Use `/wrong` command to record
- Review `[FALSE_POSITIVE]` entries in log
- Adjust keywords or patterns if needed
- Increase CHAT indicator sensitivity

---

**Issue:** Overlay doesn't show

**Solutions:**
- Check API endpoint `/detect_intent` responds
- Verify GUI method `show_clo_wizard_overlay()` called
- Check overlay widget placement in chat panel

---

**Issue:** Edits not executing

**Solutions:**
- Verify CLO_WIZARD mode actually activated
- Check `clo_api.py` `/iterate` endpoint
- Review `garment_editor` logs
- Ensure design state has `current_file`

---

## 📊 **METRICS & ANALYSIS**

### **Reading Autorouter Log**

Extract statistics:

```python
import re
from collections import Counter

with open("Logs/clo_autorouter.log", 'r') as f:
    lines = f.readlines()
    
    modes = []
    confidences = []
    
    for line in lines:
        if "MODE:" in line:
            mode_match = re.search(r"MODE:(\w+)", line)
            conf_match = re.search(r"Confidence:([\d.]+)", line)
            
            if mode_match:
                modes.append(mode_match.group(1))
            if conf_match:
                confidences.append(float(conf_match.group(1)))
    
    print(f"EDIT: {modes.count('EDIT')}, CHAT: {modes.count('CHAT')}")
    print(f"Avg Confidence: {sum(confidences)/len(confidences):.2f}")
```

### **Performance**

- Intent detection: < 50ms (keyword-based)
- LLM classification: ~200-500ms (if used)
- Total routing overhead: < 1 second

---

## ✅ **SUCCESS CRITERIA**

After implementing Phase 6:

- ✅ Single continuous chat experience
- ✅ Per-message automatic routing
- ✅ Visual overlay + color prefixes
- ✅ Logs show correct routing decisions
- ✅ Design edits execute + preview regenerate
- ✅ No mode-switch commands required
- ✅ User feedback loop functional (`/wrong`)
- ✅ Diagnostics include AutoRouter checks

---

## 🎯 **FUTURE ENHANCEMENTS**

Planned improvements:

1. **Confidence Display**
   - Show confidence score in GUI
   - Allow user to see detection reasoning

2. **Custom Patterns**
   - User-defined regex patterns
   - Per-user keyword preferences

3. **Learning from Feedback**
   - Auto-adjust confidence thresholds
   - Retrain using false positive data

4. **Multi-Turn Context**
   - Consider previous messages in detection
   - "Make it" refers to previous edit

---

**Happy Seamless Chat! 💬🔧**

*CLO Companion v6.0.0-Julian-HybridChat*




