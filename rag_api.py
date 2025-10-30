"""
Local Flask API Server for Obsidian Integration
Exposes RAG system as HTTP endpoints for ChatGPT MD plugin
"""

import sys
import os
import time

# Force UTF-8 encoding for console output (prevents UnicodeEncodeError)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_llm import answer, retrieve_local_context, save_conversation
from logger import log, log_exception
import subprocess
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow Obsidian to call this API

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "Obsidian RAG API"})

@app.route('/query', methods=['POST'])
def query():
    """Main query endpoint"""
    try:
        data = request.json
        query_text = data.get('query', '')
        use_web = data.get('use_web', False)
        reasoning_mode = data.get('reasoning_mode', 'Analytical')
        
        if not query_text:
            return jsonify({"error": "Query is required"}), 400
        
        # Get response from RAG system
        response, sources, web_note = answer(
            query_text,
            use_web_fallback=use_web,
            reasoning_mode=reasoning_mode
        )
        
        # Save conversation
        conversation_path = save_conversation(query_text, response, sources)
        
        return jsonify({
            "response": response,
            "sources": sources,
            "web_note": web_note,
            "conversation_path": conversation_path
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/retrieve', methods=['POST'])
def retrieve():
    """Retrieval-only endpoint (no LLM call)"""
    try:
        data = request.json
        query_text = data.get('query', '')
        n_results = data.get('n_results', 5)
        
        if not query_text:
            return jsonify({"error": "Query is required"}), 400
        
        contexts, distance, sources = retrieve_local_context(query_text, n_results)
        
        return jsonify({
            "contexts": contexts,
            "average_distance": distance,
            "sources": sources
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reindex', methods=['POST'])
def trigger_index():
    """Trigger document re-indexing"""
    try:
        script_path = os.path.join(os.path.dirname(__file__), "index_documents.py")
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=os.path.dirname(__file__)
        )
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": "Indexing completed",
                "output": result.stdout
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Indexing failed",
                "error": result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/index', methods=['POST'])
def trigger_index_alias():
    """Alias for /reindex"""
    return trigger_index()

@app.route('/summarize', methods=['POST'])
def summarize():
    """Summarize a provided file or text"""
    try:
        data = request.json
        file_path = data.get('file_path', '')
        text = data.get('text', '')
        summary_length = data.get('length', 'medium')  # short, medium, long
        
        if not file_path and not text:
            return jsonify({"error": "Either file_path or text is required"}), 400
        
        # If file_path provided, read the file
        if file_path:
            from query_llm import VAULT_PATH
            full_path = os.path.join(VAULT_PATH, file_path) if not os.path.isabs(file_path) else file_path
            
            if not os.path.exists(full_path):
                return jsonify({"error": f"File not found: {full_path}"}), 404
            
            # Extract text based on file type
            if full_path.endswith('.md') or full_path.endswith('.txt'):
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            elif full_path.endswith('.pdf'):
                from PyPDF2 import PdfReader
                pdf = PdfReader(full_path)
                text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            elif full_path.endswith('.docx'):
                from docx import Document
                doc = Document(full_path)
                text = "\n".join([p.text for p in doc.paragraphs])
        
        # Determine summary length
        length_prompts = {
            'short': 'Provide a brief summary (2-3 sentences)',
            'medium': 'Provide a concise summary (one paragraph)',
            'long': 'Provide a detailed summary with key points'
        }
        length_instruction = length_prompts.get(summary_length, length_prompts['medium'])
        
        # Get LLM summary
        prompt = f"""Summarize the following text. {length_instruction}

TEXT:
{text[:5000]}

SUMMARY:"""
        
        # Call Ollama directly
        result = subprocess.run(
            ["ollama", "run", "llama3.2", prompt],
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8"
        )
        summary = result.stdout.strip() if result.returncode == 0 else "Error generating summary"
        
        return jsonify({
            "summary": summary,
            "source": file_path if file_path else "provided_text",
            "length": summary_length
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/plan_essay', methods=['POST'])
def plan_essay():
    """Build a structured essay plan with citations"""
    try:
        data = request.json
        topic = data.get('topic', '')
        essay_type = data.get('type', 'academic')  # academic, argumentative, analytical
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        
        # Retrieve relevant context
        contexts, avg_distance, sources = retrieve_local_context(topic, n_results=10)
        
        # Build essay plan prompt
        context_block = "\n\n".join(contexts[:5]) if contexts else "No specific local context found."
        
        essay_type_instructions = {
            'academic': 'academic research paper with introduction, literature review, analysis, and conclusion',
            'argumentative': 'argumentative essay with thesis statement, supporting arguments, counterarguments, and conclusion',
            'analytical': 'analytical essay with clear analytical framework, evidence-based analysis, and synthesis'
        }
        type_instruction = essay_type_instructions.get(essay_type, essay_type_instructions['academic'])
        
        prompt = f"""Create a detailed essay plan for the following topic. The plan should be structured for a {type_instruction}.

RELEVANT CONTEXT FROM YOUR NOTES:
{context_block}

ESSAY TOPIC:
{topic}

Create a comprehensive essay plan with:
1. Title suggestion
2. Introduction outline (hook, background, thesis)
3. Main body structure (sections with key points)
4. Conclusion outline
5. Key sources and citations from the context provided

Format with clear sections and bullet points. Include citations in format [Source: filename, lines X-Y] where appropriate.

ESSAY PLAN:"""
        
        # Call Ollama directly
        result = subprocess.run(
            ["ollama", "run", "llama3.2", prompt],
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8"
        )
        plan = result.stdout.strip() if result.returncode == 0 else "Error generating essay plan"
        
        return jsonify({
            "plan": plan,
            "topic": topic,
            "type": essay_type,
            "sources": sources,
            "has_local_context": len(contexts) > 0
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/v1/chat/completions', methods=['POST'])
@app.route('/v1/api/chat', methods=['POST'])  # Alias for ChatGPT MD compatibility
@app.route('/v1/completions', methods=['POST'])  # Additional alias
def chat_completions():
    """OpenAI-compatible endpoint for ChatGPT MD plugin"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        messages = data.get('messages', [])
        model = data.get('model', 'local-rag-llama3.2')

        # Extract query from messages (last user message)
        query_text = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                query_text = msg.get('content', '')
                break

        if not query_text:
            return jsonify({
                "error": {
                    "message": "No user message found in request",
                    "type": "invalid_request_error"
                }
            }), 400

        # Get reasoning mode from system message if present
        reasoning_mode = "Analytical"
        for msg in messages:
            if msg.get('role') == 'system':
                system_content = msg.get('content', '')
                if 'concise' in system_content.lower():
                    reasoning_mode = "Concise"
                elif 'creative' in system_content.lower():
                    reasoning_mode = "Creative Academic"

        # Call RAG system with error handling
        try:
            response_text, sources, web_note = answer(
                query_text,
                use_web_fallback=False,  # Control via system prompt
                reasoning_mode=reasoning_mode
            )
            
            # Check if response indicates an error
            if response_text.startswith("Error:") or "Error calling local LLM" in response_text:
                error_msg = response_text.replace("Error: ", "").replace("Error calling local LLM.", "").strip()
                if not error_msg:
                    error_msg = "Failed to get response from local LLM. Please check if Ollama is running."
                
                error_response = f"I apologize, but I encountered an issue: {error_msg}. Please ensure Ollama is running and try again."
                prompt_words = len(query_text.split())
                
                return jsonify({
                    "id": f"chatcmpl-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": error_response
                        }
                    }],
                    "usage": {
                        "prompt_tokens": prompt_words,
                        "completion_tokens": len(error_response.split()),
                        "total_tokens": prompt_words + len(error_response.split())
                    }
                })
        except Exception as llm_error:
            # Handle errors from the RAG system
            error_msg = str(llm_error)
            error_response = f"I apologize, but I encountered an error processing your request: {error_msg}. Please check if Ollama is running and the RAG system is properly configured."
            prompt_words = len(query_text.split())
            
            return jsonify({
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": error_response
                    }
                }],
                "usage": {
                    "prompt_tokens": prompt_words,
                    "completion_tokens": len(error_response.split()),
                    "total_tokens": prompt_words + len(error_response.split())
                }
            })

        # Format as strict OpenAI-compatible response
        prompt_words = len(query_text.split())
        completion_words = len(final_answer.split())
        
        log(f"Query processed successfully. Response length: {completion_words} tokens", "API")
        
        return jsonify({
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": final_answer
                }
            }],
            "usage": {
                "prompt_tokens": prompt_words,
                "completion_tokens": completion_words,
                "total_tokens": prompt_words + completion_words
            }
        })

    except Exception as e:
        log_exception("API", e, "chat_completions endpoint error")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "internal_server_error"
            }
        }), 500

@app.route('/tags', methods=['GET'])
def get_tags():
    """Get all tags or tags for a specific document"""
    try:
        from semantic_tagging import get_all_tags, get_tags_for_document
        
        document_path = request.args.get('document')
        
        if document_path:
            # Get tags for specific document
            tags = get_tags_for_document(document_path)
            return jsonify({
                "document": document_path,
                "tags": tags
            })
        else:
            # Get all unique tags
            all_tags = get_all_tags()
            return jsonify({
                "all_tags": all_tags,
                "count": len(all_tags)
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    try:
        print("🚀 Starting Obsidian RAG API server...")
        print("📡 API available at: http://127.0.0.1:5000")
        print("📚 Endpoints:")
        print("   POST /query - Query with RAG and citations")
        print("   POST /retrieve - Retrieve context only")
        print("   POST /reindex - Re-index documents")
        print("   POST /summarize - Summarize file or text")
        print("   POST /plan_essay - Create structured essay plan")
        print("   POST /v1/chat/completions - OpenAI-compatible (for ChatGPT MD)")
        print("   GET /tags - Get document tags")
        print("   GET /health - Health check")
        print("\nPress Ctrl+C to stop\n")
    except UnicodeEncodeError:
        # Fallback for systems that can't print emoji
        print("Starting Obsidian RAG API server...")
        print("API available at: http://127.0.0.1:5000")
        print("Endpoints: /query, /retrieve, /reindex, /summarize, /plan_essay")
        print("OpenAI-compatible: /v1/chat/completions")
        print("Press Ctrl+C to stop\n")
    
    app.run(host='127.0.0.1', port=5000, debug=False)

