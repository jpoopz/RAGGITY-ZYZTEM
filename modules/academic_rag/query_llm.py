"""
Query LLM with RAG - Citation-Aware Academic Reasoning
Searches local knowledge base, adds citations, and optionally uses web fallback
"""

import chromadb
import json
import sys
import os
import time
from datetime import datetime
from pathlib import Path

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Import unified logger
try:
    from logger import log, log_exception
except ImportError:
    # Fallback if logger not available
    def log(msg, category="INFO", print_to_console=True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{category}] {msg}", file=sys.stderr if not print_to_console else sys.stdout)
    
    def log_exception(category="ERROR", exception=None, context=""):
        import traceback
        print(f"[{category}] {context}: {exception}", file=sys.stderr)
        traceback.print_exc()

# Import LLM connector
try:
    from core.llm_connector import LLMConnector
    llm_connector = LLMConnector()
except ImportError:
    log("Warning: LLMConnector not available, some features may be limited", "LLM")
    llm_connector = None

# Configuration - load from config
try:
    from core.config_manager import get_module_config
    module_config = get_module_config("academic_rag")
    VAULT_PATH = module_config.get("vault_path", os.path.expanduser(r"C:\Users\Julian Poopat\Documents\Obsidian"))
    NOTES_PATH = os.path.join(VAULT_PATH, module_config.get("notes_path", "Notes"))
except:
    VAULT_PATH = os.path.expanduser(r"C:\Users\Julian Poopat\Documents\Obsidian")
    NOTES_PATH = os.path.join(VAULT_PATH, "Notes")

CONVERSATIONS_PATH = os.path.join(VAULT_PATH, "Notes", "AI_Conversations")
THRESHOLD = 0.6  # Similarity threshold for web fallback

try:
    from core.config_manager import get_module_config
    module_config = get_module_config("academic_rag")
    rag_config = module_config.get("rag", {})
    OLLAMA_MODEL = rag_config.get("model", "llama3.2")
except:
    OLLAMA_MODEL = "llama3.2"

# Initialize ChromaDB - use RAG_System folder location
RAG_SYSTEM_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMADB_PATH = os.path.join(RAG_SYSTEM_PATH, ".chromadb")
try:
    client = chromadb.PersistentClient(path=CHROMADB_PATH)
    collection = client.get_collection("obsidian_docs")
    log("Connected to vector database", "LLM")
except Exception as e:
    log_exception("LLM", e, "Error connecting to database")
    sys.exit(1)

def retrieve_local_context(query, n_results=5):
    """Retrieve relevant chunks from local knowledge base"""
    try:
        # Query with tag filtering if tags are available in query context
        # For now, basic query (can be enhanced with tag-based filtering)
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # If results have tags metadata, could prioritize matching tags
        # Future enhancement: re-rank by tag relevance
        
        if not results["documents"] or not results["documents"][0]:
            return [], 1.0, []
        
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if "distances" in results else [1.0] * len(documents)
        
        # Format with citations
        formatted_contexts = []
        sources = []
        
        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            source_name = meta.get("source", "Unknown")
            line_start = meta.get("line_start", "?")
            line_end = meta.get("line_end", "?")
            
            # Create citation tag
            citation = f"[Source: {source_name}, lines {line_start}-{line_end}]"
            formatted_contexts.append(f"{citation}\n{doc[:500]}...")
            sources.append({
                "source": source_name,
                "path": meta.get("source_path", ""),
                "lines": f"{line_start}-{line_end}",
                "similarity": 1 - dist if dist <= 1.0 else 0.0
            })
        
        avg_distance = sum(distances) / len(distances) if distances else 1.0
        
        log(f"Retrieved {len(formatted_contexts)} context chunks (avg distance: {avg_distance:.3f})", "LLM")
        return formatted_contexts, avg_distance, sources
        
    except Exception as e:
        log_exception("LLM", e, "Retrieval error")
        return [], 1.0, []

def call_local_llm(prompt, max_retries=3, retry_delay=2):
    """
    Call LLM via LLMConnector with retry logic
    
    Args:
        prompt: The prompt to send to the LLM
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Seconds to wait between retries (default: 2)
    
    Returns:
        str: LLM response text, or error message starting with "Error:"
    """
    # Use LLMConnector (supports both Ollama and OpenAI)
    if llm_connector:
        for attempt in range(1, max_retries + 1):
            try:
                log(f"Calling LLM via connector (attempt {attempt}/{max_retries})...", "LLM")
                
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ]
                
                response = llm_connector.chat(messages)
                
                if response.startswith("Error:"):
                    if attempt < max_retries:
                        log(f"LLM error, retrying in {retry_delay} seconds...", "LLM")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return response
                
                log(f"LLM call successful (response length: {len(response)} chars)", "LLM")
                return response
                
            except Exception as e:
                if attempt < max_retries:
                    log(f"Error on attempt {attempt}, retrying: {e}", "LLM")
                    time.sleep(retry_delay)
                    continue
                else:
                    log_exception("LLM", e, "Error calling LLM via connector")
                    return f"Error: {str(e)}"
        
        return "Error: Failed to get response from LLM after multiple attempts."
    else:
        return "Error: LLMConnector not available. Please check configuration."

def web_fallback(query):
    """Trigger web search fallback via Cursor browser or manual note"""
    web_imports_path = os.path.join(VAULT_PATH, "Notes", "Web_Imports")
    os.makedirs(web_imports_path, exist_ok=True)
    
    # Create a note for manual web search results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    web_note = os.path.join(web_imports_path, f"web_search_{timestamp}.md")
    
    with open(web_note, "w", encoding="utf-8") as f:
        f.write(f"# Web Search Results: {query}\n\n")
        f.write(f"**Query:** {query}\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write("## Results\n\n")
        f.write("_Use Cursor browser extension or manual search to add results here_\n\n")
        f.write("## Summary\n\n")
        f.write("_\n")
    
    return f"Web search note created: {os.path.relpath(web_note, VAULT_PATH)}\nAdd search results manually or use Cursor browser to populate."

def format_response_with_citations(response, sources):
    """Format response with proper citations"""
    if not sources:
        return response
    
    # Add citations section
    citations_text = "\n\n---\n\n## Citations\n\n"
    for i, source in enumerate(sources, 1):
        citations_text += f"{i}. {source['source']}"
        if source.get('lines'):
            citations_text += f" (lines {source['lines']})"
        if source.get('path'):
            citations_text += f" - `{source['path']}`"
        citations_text += f"\n"
    
    return response + citations_text

def answer(query, use_web_fallback=False, reasoning_mode="Analytical", context_graph=None):
    """Main query answering function"""
    
    # Retrieve local context
    contexts, avg_distance, sources = retrieve_local_context(query)
    
    # Check if we need web fallback
    needs_web = avg_distance > THRESHOLD or len(contexts) == 0
    
    if needs_web and use_web_fallback:
        print("🌐 Similarity below threshold - triggering web fallback...", file=sys.stderr)
        web_note = web_fallback(query)
    else:
        web_note = None
    
    # Build prompt based on reasoning mode
    mode_configs = {
        "Concise": {"temperature_note": "be concise and direct", "citation_depth": "brief"},
        "Analytical": {"temperature_note": "provide thorough analysis", "citation_depth": "detailed"},
        "Creative Academic": {"temperature_note": "be creative while maintaining academic rigor", "citation_depth": "comprehensive"}
    }
    
    mode_config = mode_configs.get(reasoning_mode, mode_configs["Analytical"])
    
    # Construct prompt
    context_block = "\n\n".join(contexts) if contexts else "No relevant local context found."
    
    if web_note:
        context_block += f"\n\n[Web Search Note: {web_note}]"
    
    # Add memory facts to context if available
    memory_block = ""
    if context_graph:
        memory_facts = context_graph.get("memory", {}).get("facts", [])
        if memory_facts:
            memory_block = "\n\nUSER PREFERENCES & MEMORY:\n"
            for fact in memory_facts[:5]:  # Top 5 facts
                memory_block += f"- {fact.get('key', '')}: {fact.get('value', '')}\n"
    
    prompt = f"""You are a research assistant integrated with a local academic knowledge base.
Your workspace contains Management class notes and documents indexed for retrieval.

Your task is to answer questions using the provided context and cite sources inline when referencing information.

Reasoning Mode: {reasoning_mode}
{mode_config['temperature_note']}
Provide citations in the format: [Source: filename, lines X-Y] when referencing specific information.

LOCAL CONTEXT:
{context_block}
{memory_block}

USER QUESTION:
{query}

Provide a comprehensive answer with proper inline citations. If information is not in the context, state that clearly.
End with a summary if appropriate.
"""
    
    # Learn preferences from query (if detected)
    try:
        from core.memory_manager import get_memory_manager
        memory = get_memory_manager()
        
        # Detect preference cues
        if "concise" in query.lower() or "brief" in query.lower():
            memory.remember("julian", "prefers_concise", True, category="preferences")
            log("Learned preference: prefers_concise=True", "LLM")
    except:
        pass
    
    # Get LLM response
    response = call_local_llm(prompt)
    
    # Clean response for Obsidian (normalize spacing)
    response = response.strip()
    while "\n\n\n" in response:
        response = response.replace("\n\n\n", "\n\n")
    
    # Format with citations
    formatted_response = format_response_with_citations(response, sources)
    
    log(f"Query answered. Response length: {len(formatted_response)} chars, {len(sources)} sources", "LLM")
    
    return formatted_response, sources, web_note

def save_conversation(query, response, sources):
    """Save conversation to Obsidian"""
    os.makedirs(CONVERSATIONS_PATH, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"{timestamp}_query.md"
    filepath = os.path.join(CONVERSATIONS_PATH, filename)
    
    # Append to daily conversation file
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"\n## Query: {query}\n\n")
        f.write(f"**Time:** {datetime.now().strftime('%H:%M:%S')}\n\n")
        f.write("### Response\n\n")
        f.write(response)
        f.write("\n\n---\n\n")
    
    return filepath

if __name__ == "__main__":
    if len(sys.argv) < 2:
        query = input("Ask: ")
    else:
        query = " ".join(sys.argv[1:])
    
    # Parse optional flags
    use_web = "--web" in sys.argv or "-w" in sys.argv
    reasoning_mode = "Analytical"
    if "--concise" in sys.argv or "-c" in sys.argv:
        reasoning_mode = "Concise"
    elif "--creative" in sys.argv:
        reasoning_mode = "Creative Academic"
    
    print(f"🔍 Query: {query}", file=sys.stderr)
    print(f"📊 Mode: {reasoning_mode}", file=sys.stderr)
    
    response, sources, web_note = answer(query, use_web_fallback=use_web, reasoning_mode=reasoning_mode)
    
    # Save conversation
    conversation_path = save_conversation(query, response, sources)
    
    # Output response
    print(response)
    
    if web_note:
        print(f"\n📄 {web_note}", file=sys.stderr)
    
    print(f"\n💾 Saved to: {os.path.relpath(conversation_path, VAULT_PATH)}", file=sys.stderr)

