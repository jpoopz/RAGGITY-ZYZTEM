# ChatGPT MD Plugin Integration

## Configure ChatGPT MD to Use RAG API

### Method 1: Direct API Integration (If Supported)

**Settings → ChatGPT MD:**

1. **API Provider:** Select "Custom OpenAI API" or "OpenAI Compatible"
2. **API Base URL:** `http://127.0.0.1:5000/v1`
   - **Note:** RAG API uses `/query` endpoint, not `/v1/chat/completions`
   - May need adapter layer

### Method 2: System Prompt Enhancement (Recommended)

Since ChatGPT MD works directly with Ollama, enhance it with RAG context:

**Settings → ChatGPT MD → System Prompt:**

```
You are connected to a local NotebookLM-style academic assistant that indexes Obsidian notes and can call external web searches via Cursor when needed.

IMPORTANT CONTEXT INSTRUCTIONS:
1. You have access to a local knowledge base via RAG API at http://127.0.0.1:5000
2. Always use local notes as primary context for answers
3. Cite sources inline using format: [Source: filename, lines X-Y]
4. If information is missing from local knowledge, mention calling #websearch via Cursor
5. Provide comprehensive, academic-quality responses with proper citations

When answering questions:
- First, consider if the user's notes contain relevant information
- Reference specific documents when providing information
- If local context is insufficient, suggest: "This information may not be in your local notes. Use #websearch via Cursor to retrieve current information."
- Format citations as: [Source: Lecture1.md, lines 45-78]

Your responses should be analytical, well-cited, and reference the user's academic materials.
```

### Method 3: Hybrid Workflow (Best Approach)

Use both systems together:

1. **For citation-aware queries:** Use RAG system directly
   ```powershell
   python query_helper.py query "What are management theories?"
   ```

2. **For conversational follow-up:** Use ChatGPT MD with Ollama
   - The RAG response provides context
   - ChatGPT MD can continue the conversation

3. **In your notes:** Add RAG responses and continue chatting

## Workflow Example

1. **Start with RAG query:**
   - PowerShell: `python query_helper.py query "Strategic management"`
   - Gets answer with citations from your notes

2. **Copy RAG response into Obsidian note**

3. **Continue with ChatGPT MD:**
   - Ask follow-up questions
   - Reference the RAG response
   - Build on the cited information

## Quick Commands Integration

Create Quick Add macros for:

**#ask {query}**
- Command: `python query_helper.py query "{query}"`

**#reindex**
- Command: `python query_helper.py reindex`

**#summarize {file}**
- Command: `python query_helper.py summarize "{file}"`

**#plan {topic}**
- Command: `python query_helper.py plan "{topic}"`

Then use these commands directly in Obsidian!

## API Adapter (If Needed)

If ChatGPT MD requires `/v1/chat/completions` format, create adapter:

```python
# Add to rag_api.py
@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """OpenAI-compatible endpoint for ChatGPT MD"""
    data = request.json
    messages = data.get('messages', [])
    
    # Extract query from messages
    query_text = messages[-1].get('content', '') if messages else ''
    
    # Call RAG system
    response, sources, _ = answer(query_text)
    
    # Format as OpenAI response
    return jsonify({
        "choices": [{
            "message": {
                "role": "assistant",
                "content": response
            },
            "finish_reason": "stop"
        }],
        "model": "local-rag-llama3",
        "usage": {"total_tokens": len(response.split())}
    })
```

Then set ChatGPT MD API URL to: `http://127.0.0.1:5000/v1`




