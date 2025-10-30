# Memory System Schema - Database Structure

**Database:** `memory.db` (SQLite)  
**Location:** Project root directory

---

## 📊 **Database Tables**

### 1. `facts` Table

Stores user facts, preferences, and learned information.

**Schema:**
```sql
CREATE TABLE facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user, key)
)
```

**Columns:**
- `id` - Auto-increment primary key
- `user` - User identifier (e.g., "julian")
- `key` - Fact key (e.g., "prefers_concise", "favorite_subject")
- `value` - Fact value (JSON-encoded if complex)
- `category` - Optional category (e.g., "preferences", "knowledge", "queries")
- `created_at` - First creation timestamp
- `updated_at` - Last update timestamp

**Unique Constraint:** `(user, key)` - One fact per key per user

**Example Data:**
```
user: "julian"
key: "prefers_concise"
value: "true"
category: "preferences"
```

---

### 2. `sessions` Table

Tracks user sessions for analytics and summarization.

**Schema:**
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    session_id TEXT NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    summary TEXT,
    facts_learned INTEGER DEFAULT 0,
    UNIQUE(user, session_id)
)
```

**Columns:**
- `id` - Auto-increment primary key
- `user` - User identifier
- `session_id` - Unique session identifier
- `start_time` - Session start timestamp
- `end_time` - Session end timestamp (NULL if active)
- `summary` - Optional session summary text
- `facts_learned` - Count of facts learned this session

**Example Data:**
```
user: "julian"
session_id: "session_20251029_180000"
start_time: "2025-10-29T18:00:00"
end_time: "2025-10-29T19:30:00"
facts_learned: 3
```

---

### 3. `log_summaries` Table

Stores periodic summaries of logs and activity.

**Schema:**
```sql
CREATE TABLE log_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    period_start DATETIME NOT NULL,
    period_end DATETIME NOT NULL,
    summary_text TEXT,
    key_insights TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Columns:**
- `id` - Auto-increment primary key
- `user` - User identifier
- `period_start` - Start of summary period
- `period_end` - End of summary period
- `summary_text` - Full summary text
- `key_insights` - Key insights extracted (JSON or text)
- `created_at` - When summary was created

**Auto-Summarization:** Runs every 6 hours, extracts:
- Preference patterns
- Error patterns
- Frequently asked questions
- Usage trends

---

## 🔍 **Usage Examples**

### Remember a Fact

```python
from core.memory_manager import get_memory_manager

memory = get_memory_manager()
memory.remember("julian", "prefers_concise", True, category="preferences")
memory.remember("julian", "favorite_subject", "Strategic Management", category="academic")
memory.remember("julian", "last_rag_query", "What is sensemaking?", category="queries")
```

### Recall a Fact

```python
prefers_concise = memory.recall("julian", "prefers_concise", default=False)
favorite = memory.recall("julian", "favorite_subject", default="None")
```

### Get Context Bundle

```python
# Get top 10 most recent facts
facts = memory.context_bundle("julian", limit=10)

# Get preferences only
prefs = memory.context_bundle("julian", limit=5, category="preferences")
```

### Get All Facts

```python
all_facts = memory.get_all_facts("julian")
# Returns: {"prefers_concise": True, "favorite_subject": "Strategic Management", ...}
```

### Start/End Session

```python
session_id = memory.start_session("julian")
# ... use system ...
memory.end_session("julian", session_id, summary="Worked on management essay")
```

---

## 📈 **Data Flow**

```
User Query
    ↓
Context Graph Builder
    ↓
Memory Manager (top-K facts)
    ↓
Combined with RAG documents
    ↓
Sent to LLM
    ↓
Response returned
    ↓
Learn new preferences (if detected)
    ↓
Store in memory.db
```

---

## 🔒 **Best Practices**

1. **Use Categories:** Organize facts by category (preferences, knowledge, queries)
2. **Limit Values:** Keep fact values concise (< 500 chars recommended)
3. **JSON Encoding:** Complex values auto-encoded as JSON
4. **Regular Cleanup:** Old facts can be archived or removed
5. **Privacy:** All data stored locally in SQLite (no cloud)

---

## 🛠️ **Maintenance**

### View Database

```bash
sqlite3 memory.db
.tables
SELECT * FROM facts WHERE user = 'julian';
.quit
```

### Backup

```bash
cp memory.db memory.db.backup
```

### Reset Memory

```bash
rm memory.db  # Will be recreated on next run
```

---

**Memory System Status:** ✅ Operational  
**Auto-Summarization:** Every 6 hours  
**Size:** Typically < 10 MB




