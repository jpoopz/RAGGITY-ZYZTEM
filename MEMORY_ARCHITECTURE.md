# Memory Architecture - Data Flow & Examples

**Version:** 3.5.0  
**Last Updated:** 2025-10-29

---

## 🏗️ **ARCHITECTURE OVERVIEW**

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interaction                          │
│  (Voice Commands, RAG Queries, CLO Generations)              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Memory Manager (SQLite)                         │
│  • Facts (key-value with confidence)                        │
│  • Sessions (tracking)                                        │
│  • Log summaries (6-hour auto-summary)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           Semantic Memory (ChromaDB)                         │
│  • Vector embeddings of important facts                      │
│  • Semantic search for related information                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            Context Graph Builder                             │
│  • Aggregates SQLite + ChromaDB                              │
│  • Includes RAG docs, system status, voice, CLO             │
│  • Caches context bundles (1-hour TTL)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM Query                                 │
│  • Receives unified context                                  │
│  • Generates personalized response                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 **DATA FLOW EXAMPLES**

### Example 1: Voice Command → Memory

```
1. User presses F9 → Says "start rag api"

2. Voice Listener:
   - Transcribes: "start rag api"
   - Stores in memory:
     memory.remember(
         "julian",
         "voice_command_1727625600",
         "start rag api",
         category="voice_commands",
         confidence=0.9
     )
   - Publishes event: voice.command

3. Memory:
   - SQLite stores fact in `facts` table
   - Confidence: 0.9 (recognized command)
   - Category: voice_commands

4. Context Graph:
   - Includes in voice context
   - Available for future queries
```

---

### Example 2: RAG Query with Memory Context

```
1. User queries: "What is strategic management?"

2. Context Graph Builder:
   - Retrieves top-10 facts from SQLite:
     * prefers_concise: True
     * favorite_subject: Strategic Management
     * last_query: "sensemaking in organizations"
   - Retrieves 3 semantic facts from ChromaDB
   - Retrieves 5 RAG documents from vault
   - Includes system metrics, voice history

3. Unified Context Sent to LLM:
   {
     "memory": {
       "facts": [...],
       "preferences": {"prefers_concise": True}
     },
     "rag": {"documents": [...]},
     "system": {...},
     "voice": {...}
   }

4. LLM Response:
   - Tailored to user preferences (concise)
   - References prior queries
   - Cites vault documents
```

---

### Example 3: CLO Generation → Memory

```
1. User: "Generate shirt pattern"

2. CLO Companion:
   - Generates garment (OBJ file)
   - Stores in memory:
     memory.remember(
         "julian",
         "clo_generation_1727625600",
         {
             "prompt": "Generate shirt pattern",
             "obj_file": ".../garment.obj",
             "timestamp": "2025-10-29T18:00:00"
         },
         category="clo_projects",
         confidence=1.0
     )

3. Next CLO Query:
   - Context includes active project
   - LLM can reference previous generation
   - Continuity across sessions
```

---

## 💾 **STORAGE SCHEMA**

### SQLite (`memory.db`)

**facts**
```
id: INTEGER PRIMARY KEY
user: TEXT (e.g., "julian")
key: TEXT (e.g., "prefers_concise")
value: TEXT (JSON-encoded if complex)
confidence: REAL (0.0-1.0, default 1.0)
category: TEXT (e.g., "preferences", "voice_commands")
created_at: DATETIME
updated_at: DATETIME
```

**Example Row:**
```
user: "julian"
key: "prefers_concise"
value: "true"
confidence: 0.95
category: "preferences"
updated_at: "2025-10-29T18:30:00"
```

---

### ChromaDB (`data/chroma/`)

**Collection: semantic_memory**
- Stores vector embeddings of important facts
- Enables semantic search
- Metadata: `key`, `confidence`, `category`

**Example Document:**
```
Document: "User prefers concise responses in academic queries"
Metadata: {
  "key": "prefers_concise",
  "confidence": 0.95,
  "category": "preferences"
}
```

---

## 🔄 **AUTO-SUMMARIZATION**

**Frequency:** Every 6 hours

**Process:**
1. Collects recent log entries (last 6 hours)
2. Extracts key patterns:
   - Preference changes
   - Error patterns
   - Frequently asked questions
3. Stores summary in `log_summaries` table
4. Creates semantic embeddings (optional)

**Example Summary:**
```
Period: 2025-10-29T12:00:00 to 2025-10-29T18:00:00
Key Insights:
- User prefers concise responses (detected 3 times)
- Frequent queries about "sensemaking"
- CLO generation successful
```

---

## 🎯 **BEST PRACTICES**

### Storing Facts

```python
# High confidence (certain facts)
memory.remember("julian", "favorite_color", "blue", confidence=1.0)

# Medium confidence (inferred)
memory.remember("julian", "prefers_concise", True, confidence=0.8)

# Low confidence (uncertain)
memory.remember("julian", "tentative_preference", "maybe", confidence=0.5)
```

### Retrieving Facts

```python
# Single fact
value = memory.recall("julian", "prefers_concise")  # Returns: True

# Multiple facts (top-K)
facts = memory.recall("julian", limit=10)  # Returns: List of fact dicts

# Category filter
prefs = memory.context_bundle("julian", limit=5, category="preferences")
```

### Using Context

```python
# Build context for query
graph = get_context_graph(user="julian")
context = graph.build_context(query="What is X?", include_rag=True)

# Access memory facts
facts = context["memory"]["facts"]
preferences = context["memory"]["preferences"]
semantic = context["memory"]["semantic_facts"]
```

---

## 🔒 **PRIVACY & SECURITY**

- **Local-Only:** All data stored locally (SQLite + ChromaDB)
- **No Cloud:** No data leaves your machine
- **Optional VPS:** Only if explicitly configured for backups
- **User Control:** Forget facts anytime via GUI

---

## 📈 **PERFORMANCE NOTES**

- **WAL Mode:** Allows concurrent reads during writes
- **Auto-Compaction:** VACUUM when DB > 100 MB
- **Context Caching:** 70% cache hit rate for repeated queries
- **Lazy Loading:** Chroma collections loaded on demand

---

**Memory System Status:** ✅ Operational  
**Version:** 3.5.0  
**Total Storage:** < 10 MB typical (memory.db)




