# Obsidian Integration Guide

## How to Use RAG System in Obsidian

### Method 1: Command Line (Quick Test)

Open PowerShell in the RAG_System folder:

```powershell
python query_llm.py "What are the key management theories?"
```

### Method 2: Via API Server

1. **Start the API server:**
   ```bash
   start_api.bat
   # Or: python rag_api.py
   ```

2. **In Obsidian, use a template or Quick Add macro** that calls the API

### Method 3: Quick Add Macro

1. **Settings** → **Quick Add**
2. **Add Choice** → Name: `RAG Query`
3. **Type:** Macro
4. **Add Action:** Command → Run Command
5. **Command:**
   ```powershell
   python "C:\Users\Julian Poopat\Documents\Management Class\RAG_System\query_llm.py" "{query}"
   ```

### Method 4: Custom Obsidian Command (Advanced)

Create a JavaScript snippet that Obsidian can run:

```javascript
// Obsidian Plugin Script
const { exec } = require('child_process');
const path = require('path');

const ragScript = path.join(
    app.vault.adapter.basePath, 
    "RAG_System", 
    "query_llm.py"
);

const query = await app.prompt("Enter your question:");
if (!query) return;

exec(`python "${ragScript}" "${query}"`, (error, stdout, stderr) => {
    if (error) {
        new Notice(`Error: ${error.message}`, 5000);
        return;
    }
    
    // Create note with response
    const noteContent = `# Query: ${query}\n\n## Response\n\n${stdout}`;
    app.vault.create(`Notes/AI_Conversations/${Date.now()}.md`, noteContent);
    
    new Notice("Response saved to AI_Conversations", 3000);
});
```

## ChatGPT MD Plugin Integration

Since ChatGPT MD works directly with Ollama, we can enhance it with pre-query context retrieval:

### Enhanced System Prompt for ChatGPT MD

Add to ChatGPT MD system prompt:

```
You are connected to a local academic knowledge base that contains Management class notes and documents.

When answering questions:
1. Cite sources inline using format: [Source: filename, lines X-Y]
2. Reference specific documents when providing information
3. If information is not in your knowledge, state that clearly
4. Provide comprehensive, academic-quality responses

The knowledge base is automatically indexed and available through your responses.
```

### Workflow

1. **Query in ChatGPT MD** (normal chat)
2. **Run RAG query separately** via command or macro
3. **Copy RAG response** into your chat for context
4. **Continue conversation** with full context

### Better: Hybrid Approach

1. **Before asking in ChatGPT MD:**
   - Run RAG query: `python query_llm.py "your question"`
   - Read the retrieved sources
   - Reference them in your ChatGPT MD conversation

2. **Or use both:**
   - RAG for citation-aware factual queries
   - ChatGPT MD for conversational follow-ups with that context

## Citation Examples

When RAG system responds, citations look like:

```
Management theories include classical, behavioral, and modern approaches.

[Source: Lecture2.md, lines 45-78] The classical theory emphasizes...

[Source: Textbook.pdf, lines 120-145] Behavioral theory focuses on...
```

## Daily Workflow

1. **Morning:** Index any new documents
   ```bash
   python index_documents.py
   ```

2. **During study:**
   - Use RAG for specific questions with citations
   - Use ChatGPT MD for conversation and exploration

3. **End of day:** Check `AI_Conversations/` folder for logged queries

## API Endpoints Reference

### Query Endpoint
```bash
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is strategic management?", "reasoning_mode": "Analytical"}'
```

### Retrieve Only (No LLM)
```bash
curl -X POST http://localhost:5000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "management theories", "n_results": 5}'
```

### Re-index
```bash
curl -X POST http://localhost:5000/index
```

## Quick Commands Template

Create these as Obsidian templates or Quick Add macros:

```
#ask {query}    → python query_llm.py "{query}"
#reindex        → python index_documents.py
#websearch      → python query_llm.py "{query}" --web
```

## Troubleshooting Integration

**RAG script not found:**
- Check path in command/template
- Use absolute path: `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\query_llm.py`

**Python not in PATH:**
- Use full Python path in commands
- Or add Python to system PATH

**API not responding:**
- Check if server is running: `http://localhost:5000/health`
- Check firewall isn't blocking port 5000

---

The system is ready! Start with indexing your documents, then query away! 🚀




