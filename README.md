# Obsidian RAG System - NotebookLM-Style Academic Assistant

Complete local RAG (Retrieval Augmented Generation) system for your Management class notes with citation-aware reasoning and web fallback.

## ✅ Setup Complete!

All components have been implemented and configured. Follow the steps below to finalize.

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies

```powershell
cd "C:\Users\Julian Poopat\Documents\Management Class\RAG_System"
.\install_deps.ps1
```

Or manually:
```powershell
python -m pip install -r requirements.txt
```

### Step 2: Index Your Documents

```powershell
python index_documents.py
```

This scans `C:\Users\Julian Poopat\Documents\Obsidian\Notes` and creates searchable index.

**Time:** 5-10 minutes depending on document count

### Step 3: Start API Server

```powershell
python rag_api.py
```

Or use:
```powershell
.\start_api.bat
```

Server runs on: `http://127.0.0.1:5000`

## 📡 API Endpoints

### POST `/query`
Query with RAG and get citation-aware response.

**Request:**
```json
{
  "query": "What are management theories?",
  "use_web": false,
  "reasoning_mode": "Analytical"
}
```

**Response:**
```json
{
  "response": "Answer with [Source: filename, lines X-Y] citations...",
  "sources": [...],
  "conversation_path": "Notes/AI_Conversations/2025-10-29_query.md"
}
```

### POST `/reindex`
Re-index all documents.

**Request:** `{}`

**Response:**
```json
{
  "status": "success",
  "message": "Indexing completed"
}
```

### POST `/summarize`
Summarize a file or text.

**Request:**
```json
{
  "file_path": "Notes/Lecture1.md",
  "length": "medium"  // short, medium, long
}
```

Or:
```json
{
  "text": "Text to summarize...",
  "length": "medium"
}
```

### POST `/plan_essay`
Create structured essay plan with citations.

**Request:**
```json
{
  "topic": "Strategic Management",
  "type": "academic"  // academic, argumentative, analytical
}
```

**Response:**
```json
{
  "plan": "Detailed essay plan...",
  "sources": [...],
  "has_local_context": true
}
```

### POST `/v1/chat/completions`
OpenAI-compatible endpoint for ChatGPT MD plugin.

**Request:** (OpenAI format)
```json
{
  "model": "local-rag-llama3.2",
  "messages": [
    {"role": "user", "content": "What is management?"}
  ]
}
```

### POST `/retrieve`
Retrieve context only (no LLM call).

**Request:**
```json
{
  "query": "management theories",
  "n_results": 5
}
```

### GET `/health`
Health check endpoint.

## 🔌 ChatGPT MD Plugin Integration

### Configuration

1. **Settings → ChatGPT MD**

2. **Option A: Use RAG API Directly**
   - **API Provider:** "OpenAI Compatible" or "Custom OpenAI API"
   - **API Base URL:** `http://127.0.0.1:5000/v1`
   - **Model:** `local-rag-llama3.2`
   - **API Key:** (leave empty)

3. **Option B: Enhanced System Prompt** (Recommended)
   - Keep using Ollama directly: `http://localhost:11434/v1`
   - Model: `llama3.2`
   - **System Prompt:**
   ```
   You are connected to a local NotebookLM-style academic assistant. 
   Always use my notes as primary context. If missing info, call #websearch via Cursor. 
   Cite sources inline with [Source: filename, lines X–Y].
   ```

## 📝 Obsidian Commands

### Using Quick Add Plugin

Create these macros in Quick Add:

**#ask {query}**
- Command: `python "C:\Users\Julian Poopat\Documents\Management Class\RAG_System\query_helper.py" query "{query}"`

**#reindex**
- Command: `python "C:\Users\Julian Poopat\Documents\Management Class\RAG_System\query_helper.py" reindex`

**#summarize {file}**
- Command: `python "C:\Users\Julian Poopat\Documents\Management Class\RAG_System\query_helper.py" summarize "{file}"`

**#plan {topic}**
- Command: `python "C:\Users\Julian Poopat\Documents\Management Class\RAG_System\query_helper.py" plan "{topic}"`

## 📚 Usage Examples

### Command Line

```powershell
# Query
python query_helper.py query "What is strategic management?"

# Query with web fallback
python query_helper.py query "Recent management trends" --web

# Reindex
python query_helper.py reindex

# Summarize
python query_helper.py summarize "Notes/Lecture1.md"

# Plan essay
python query_helper.py plan "Organizational Behavior"
```

### PowerShell API Calls

```powershell
# Query
$body = @{query="What is management?"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:5000/query" -Method POST -Body $body -ContentType "application/json"

# Reindex
Invoke-RestMethod -Uri "http://127.0.0.1:5000/reindex" -Method POST

# Summarize
$body = @{file_path="Lecture1.md"; length="medium"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:5000/summarize" -Method POST -Body $body -ContentType "application/json"

# Plan essay
$body = @{topic="Strategic Management"; type="academic"} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:5000/plan_essay" -Method POST -Body $body -ContentType "application/json"
```

## 🧪 Testing

Run the test script:
```powershell
.\test_all_endpoints.ps1
```

This tests all endpoints and verifies the system is working.

## 📁 Directory Structure

```
Obsidian/
├── Notes/
│   ├── AI_Conversations/  (saved queries)
│   ├── Web_Imports/       (web search results)
│   └── [your documents]/  (indexed files)
└── ...

Management Class/
└── RAG_System/
    ├── index_documents.py     (indexer)
    ├── query_llm.py           (query processor)
    ├── rag_api.py             (Flask API server)
    ├── query_helper.py        (CLI helper)
    ├── requirements.txt       (dependencies)
    ├── install_deps.ps1       (install script)
    ├── start_api.bat          (start server)
    ├── test_all_endpoints.ps1 (test script)
    └── .chromadb/             (vector database)
```

## ⚙️ Configuration

Edit these variables in scripts:

**index_documents.py:**
- `VAULT_PATH` - Obsidian vault location
- `NOTES_PATH` - Notes directory
- `CHUNK_SIZE` - Text chunk size (default: 1000)

**query_llm.py:**
- `THRESHOLD` - Similarity threshold for web fallback (default: 0.6)
- `OLLAMA_MODEL` - Your Ollama model (default: "llama3.2")

**rag_api.py:**
- `host` - API host (default: "127.0.0.1")
- `port` - API port (default: 5000)

## 🔍 Troubleshooting

### API Server Not Starting
- Check Python is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Check port 5000 isn't in use

### Indexing Fails
- Verify Notes directory exists: `C:\Users\Julian Poopat\Documents\Obsidian\Notes`
- Check file permissions
- Ensure documents are accessible

### Queries Return Empty
- Run indexing: `python index_documents.py`
- Verify ChromaDB created: Check `.chromadb/` folder exists
- Test with: `python query_helper.py query "test"`

### Ollama Connection Issues
- Verify Ollama running: `ollama list`
- Check model name matches: `llama3.2`
- Test directly: `ollama run llama3.2 "hello"`

## 📖 Citation Format

Citations appear inline:
```
[Source: Lecture3.md, lines 45-78]
```

And in citations section:
```
## Citations
1. Lecture3.md (lines 45-78) - `Notes/Lecture3.md`
```

## 🎓 Workflow Examples

### Research Query
```powershell
python query_helper.py query "What are the main organizational theories?" --creative
```

### Essay Planning
```powershell
python query_helper.py plan "Modern Leadership Approaches" --academic
```

### Document Summarization
```powershell
python query_helper.py summarize "Notes/Week5/Management_Principles.pdf"
```

### Regular Re-indexing
After adding new notes:
```powershell
python query_helper.py reindex
```

## ✨ Features

✅ **Local Document Indexing** - All Markdown, PDF, DOCX files  
✅ **Vector Search** - Semantic search through your notes  
✅ **Automatic Citations** - Inline source citations with line numbers  
✅ **Multiple Reasoning Modes** - Concise, Analytical, Creative Academic  
✅ **Essay Planning** - Structured plans with citations  
✅ **File Summarization** - Summarize any document  
✅ **Web Fallback** - Trigger web search when needed  
✅ **Conversation Logging** - All queries saved  
✅ **OpenAI-Compatible API** - Works with ChatGPT MD  
✅ **REST API** - Full HTTP API for integration  
✅ **100% Local & Private** - All processing on your computer  

## 🎯 Next Steps

1. ✅ Install dependencies: `.\install_deps.ps1`
2. ✅ Index documents: `python index_documents.py`
3. ✅ Start API: `python rag_api.py`
4. ✅ Test endpoints: `.\test_all_endpoints.ps1`
5. ✅ Configure ChatGPT MD plugin
6. ✅ Set up Quick Add macros
7. ✅ Start using in Obsidian!

## 📞 Support

- Full documentation: See `FINAL_SETUP_COMPLETE.md`
- Integration guide: See `CHATGPT_MD_INTEGRATION.md`
- Obsidian commands: See `Notes/RAG_Commands_Template.md`

---

**You now have a fully working, offline-first, citation-aware, web-augmented academic reasoning system!** 🎓📚🚀
