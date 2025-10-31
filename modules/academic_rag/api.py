"""
Local Flask API Server for Obsidian Integration
Exposes RAG system as HTTP endpoints for ChatGPT MD plugin
"""

import sys
import os
import time

# Force UTF-8 encoding for console output (safe for GUI mode)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
from core.io_safety import safe_reconfigure_streams
safe_reconfigure_streams()

from flask import Flask, request, jsonify
from flask_cors import CORS

# Add paths for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.academic_rag.query_llm import answer, retrieve_local_context, save_conversation
from logger import get_logger
from core.config_manager import get_module_config, get_suite_config
from core.auth_helper import require_auth_token
import subprocess
from datetime import datetime

# Initialize logger
log = get_logger("academic_rag_api")

app = Flask(__name__)

# Track API start time for uptime calculation
api_start_time = time.time()

# CORS config from suite config
suite_config = get_suite_config()
if suite_config.get("security", {}).get("cors_enabled", False):
    CORS(app)

module_config = get_module_config("academic_rag")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    global api_start_time
    uptime = int(time.time() - api_start_time)
    
    return jsonify({
        "status": "healthy",
        "module_id": "academic_rag",
        "version": "4.1.0-Julian-PolishFinal",
        "uptime_seconds": uptime,
        "service": "Academic RAG API"
    })

@app.route('/health/full', methods=['GET'])
def health_full():
    """Comprehensive system health endpoint for dashboard polling"""
    try:
        from modules.academic_rag.health_endpoint import get_full_health
        return jsonify(get_full_health())
    except Exception as e:
        log.error(f"Health check failed: {e}")
        return jsonify({
            "error": str(e),
            "error_type": e.__class__.__name__
        }), 500

@app.route('/health/clo', methods=['GET'])
def health_clo():
    """Lightweight CLO Bridge health check for UI polling"""
    try:
        from modules.academic_rag.health_endpoint import get_clo_health
        return jsonify(get_clo_health())
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

@app.route('/query', methods=['POST'])
def query():
    """Main query endpoint"""
    try:
        data = request.json
        if not data:
            log.error("No JSON data provided in request")
            return jsonify({"error": "No JSON data provided"}), 400
            
        query_text = data.get('query', '')
        use_web = data.get('use_web', False)
        reasoning_mode = data.get('reasoning_mode', 'Analytical')
        
        if not query_text:
            log.warning("Query request missing query text")
            return jsonify({"error": "Query is required"}), 400
        
        log.info(f"Processing query: {query_text[:100]}...")
        
        # Get response from RAG system
        try:
            response, sources, web_note = answer(
                query_text,
                use_web_fallback=use_web,
                reasoning_mode=reasoning_mode
            )
        except Exception as e:
            log.error(f"Error generating answer: {e}")
            return jsonify({"error": f"Failed to generate answer: {str(e)}"}), 500
        
        # Save conversation
        try:
            conversation_path = save_conversation(query_text, response, sources)
        except Exception as e:
            log.warning(f"Failed to save conversation: {e}")
            conversation_path = None
        
        log.info(f"Query completed successfully, {len(sources)} sources")
        
        return jsonify({
            "response": response,
            "sources": sources,
            "web_note": web_note,
            "conversation_path": conversation_path
        })
        
    except Exception as e:
        log.error(f"Unexpected error in query endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/retrieve', methods=['POST'])
def retrieve():
    """Retrieval-only endpoint (no LLM call)"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        query_text = data.get('query', '')
        n_results = data.get('n_results', 5)
        
        if not query_text:
            log.warning("Retrieve request missing query text")
            return jsonify({"error": "Query is required"}), 400
        
        log.info(f"Retrieving contexts for: {query_text[:100]}...")
        
        try:
            contexts, distance, sources = retrieve_local_context(query_text, n_results)
        except Exception as e:
            log.error(f"Error during retrieval: {e}")
            return jsonify({"error": f"Retrieval failed: {str(e)}"}), 500
        
        log.info(f"Retrieved {len(contexts)} contexts")
        
        return jsonify({
            "contexts": contexts,
            "average_distance": distance,
            "sources": sources
        })
        
    except Exception as e:
        log.error(f"Unexpected error in retrieve endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/reindex', methods=['POST'])
def trigger_index():
    """Trigger document re-indexing"""
    try:
        log.info("Starting document re-indexing")
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index_documents.py")
        
        if not os.path.exists(script_path):
            log.error(f"Index script not found: {script_path}")
            return jsonify({"error": "Index script not found"}), 500
        
        try:
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=600,
                cwd=os.path.dirname(__file__)
            )
        except subprocess.TimeoutExpired:
            log.error("Indexing timeout after 600 seconds")
            return jsonify({"error": "Indexing timeout"}), 500
        except Exception as e:
            log.error(f"Error running index script: {e}")
            return jsonify({"error": f"Failed to run indexing: {str(e)}"}), 500
        
        if result.returncode == 0:
            log.info("Indexing completed successfully")
            return jsonify({
                "status": "success",
                "message": "Indexing completed",
                "output": result.stdout
            })
        else:
            log.error(f"Indexing failed with code {result.returncode}")
            return jsonify({
                "status": "error",
                "message": "Indexing failed",
                "error": result.stderr
            }), 500
            
    except Exception as e:
        log.error(f"Unexpected error in reindex endpoint: {e}")
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
        
        # Get LLM summary via connector
        try:
            from core.llm_connector import LLMConnector
            llm = LLMConnector()
            
            prompt = f"""Summarize the following text. {length_instruction}

TEXT:
{text[:5000]}

SUMMARY:"""
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                {"role": "user", "content": prompt}
            ]
            
            summary = llm.chat(messages)
        except Exception as e:
            log_exception("API", e, "Error generating summary")
            summary = "Error generating summary"
        
        return jsonify({
            "summary": summary,
            "source": file_path if file_path else "provided_text",
            "length": summary_length
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/context/preview', methods=['GET'])
def context_preview():
    """Preview current context graph"""
    try:
        from core.context_graph import get_context_graph
        
        query = request.args.get('query', '')
        
        try:
            graph = get_context_graph(user="julian")
            preview = graph.context_preview(query=query if query else None)
        except Exception as e:
            log.error(f"Error building context preview: {e}")
            return jsonify({"error": f"Context graph error: {str(e)}"}), 500
        
        return jsonify({
            "preview": preview,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        log.error(f"Error in context preview endpoint: {e}")
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
        
        # Call LLM via connector
        try:
            from core.llm_connector import LLMConnector
            llm = LLMConnector()
            
            messages = [
                {"role": "system", "content": "You are an academic writing assistant."},
                {"role": "user", "content": prompt}
            ]
            
            plan = llm.chat(messages)
        except Exception as e:
            log_exception("API", e, "Error generating essay plan")
            plan = "Error generating essay plan"
        
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
        
        # Get user preferences from memory
        try:
            from core.memory_manager import get_memory_manager
            memory = get_memory_manager()
            prefers_concise = memory.recall("julian", "prefers_concise", False)
            if prefers_concise:
                reasoning_mode = "Concise"
        except Exception as e:
            log.warning(f"Memory manager unavailable: {e}")
        
        # Build context graph
        try:
            from core.context_graph import get_context_graph
            graph = get_context_graph(user="julian")
            context_data = graph.build_context(query=query_text, include_rag=True)
            log(f"Context graph built: {len(context_data.get('memory', {}).get('facts', []))} facts", "API")
        except Exception as e:
            log(f"Error building context graph: {e}", "API", level="WARNING")
            context_data = None

        # Call RAG system with error handling
        try:
            response_text, sources, web_note = answer(
                query_text,
                use_web_fallback=False,  # Control via system prompt
                reasoning_mode=reasoning_mode,
                context_graph=context_data  # Pass context graph
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

        # Clean response for Obsidian (normalize spacing)
        final_answer = response_text.strip()
        while "\n\n\n" in final_answer:
            final_answer = final_answer.replace("\n\n\n", "\n\n")

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
    port = module_config.get('api', {}).get('port', 5000)
    host = suite_config.get("security", {}).get("bind_localhost_only", True)
    host_addr = "127.0.0.1" if host else "0.0.0.0"
    
    # Log Python version info
    import platform
    py_version = sys.version.split()[0]
    log.info(f"Python {py_version} | {platform.system()} {platform.release()}")
    
    try:
        log.info(f"🚀 Starting Academic RAG API server on {host_addr}:{port}")
    except UnicodeEncodeError:
        log.info(f"Starting Academic RAG API server on {host_addr}:{port}")
    
    # Verify Ollama connectivity
    try:
        from core.llm_connector import verify_ollama_setup
        success, message = verify_ollama_setup(log.info)
        if success:
            log.info(message)
        else:
            log.warning(message)
    except Exception as e:
        log.warning(f"Could not verify Ollama setup: {e}")
    
    app.run(host=host_addr, port=port, debug=False)

