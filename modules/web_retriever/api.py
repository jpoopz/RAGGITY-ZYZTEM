"""
Web Retriever Module - Flask API Server (STUB)
"""

import sys
import os

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from flask import Flask, request, jsonify
from flask_cors import CORS

# Add paths for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from logger import get_logger
    log = get_logger("web_retriever_api")
except ImportError:
    class DummyLogger:
        def info(self, msg): print(f"[WEB_RETRIEVER] {msg}")
        def error(self, msg): print(f"[WEB_RETRIEVER] ERROR: {msg}")
        def warning(self, msg): print(f"[WEB_RETRIEVER] WARNING: {msg}")
    log = DummyLogger()

from core.config_manager import get_module_config, get_suite_config
from core.auth_helper import require_auth_token

# Import web search function
try:
    from modules.web_retriever.web_search import web_search, scrape_url
    WEB_SEARCH_AVAILABLE = True
except ImportError as e:
    log.warning(f"web_search module not available: {e}")
    WEB_SEARCH_AVAILABLE = False

app = Flask(__name__)

# CORS config from suite config
suite_config = get_suite_config()
if suite_config.get("security", {}).get("cors_enabled", False):
    CORS(app)

module_config = get_module_config("web_retriever")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    # Check Cursor bridge connectivity
    cursor_bridge_healthy = False
    if WEB_SEARCH_AVAILABLE:
        try:
            from modules.cursor_bridge.client import get_cursor_bridge_client
            client = get_cursor_bridge_client()
            cursor_bridge_healthy = client.health_check()
        except:
            pass
    
    return jsonify({
        "status": "healthy",
        "module_id": "web_retriever",
        "version": "2.0.0",
        "uptime_seconds": 0,
        "cursor_bridge_connected": cursor_bridge_healthy,
        "web_search_available": WEB_SEARCH_AVAILABLE,
        "enabled": module_config.get("enabled", False)
    })

@app.route('/search', methods=['POST'])
@require_auth_token
def search():
    """Web search endpoint using Cursor bridge"""
    try:
        data = request.json or {}
        query = data.get('query', '')
        max_results = data.get('max_results', 5)
        
        if not query:
            log.warning("Search request missing query")
            return jsonify({"error": "Query is required"}), 400
        
        if not WEB_SEARCH_AVAILABLE:
            log.error("Web search not available")
            return jsonify({"error": "Web search module not available"}), 503
        
        log.info(f"Processing search request: {query[:100]}...")
        
        # Use web_search function with rate limiting
        result = web_search(query, max_results=max_results)
        
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in search endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/scrape', methods=['POST'])
@require_auth_token
def scrape():
    """Scrape URL endpoint using Cursor bridge"""
    try:
        data = request.json or {}
        url = data.get('url', '')
        
        if not url:
            log.warning("Scrape request missing URL")
            return jsonify({"error": "URL is required"}), 400
        
        if not WEB_SEARCH_AVAILABLE:
            log.error("Web search not available")
            return jsonify({"error": "Web scraping module not available"}), 503
        
        log.info(f"Processing scrape request: {url[:80]}...")
        
        # Use scrape_url function with rate limiting
        result = scrape_url(url)
        
        return jsonify(result)
        
    except Exception as e:
        log.error(f"Error in scrape endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/summarize_web', methods=['POST'])
@require_auth_token
def summarize_web():
    """Summarize web content (local or remote)"""
    try:
        data = request.json or {}
        query = data.get('query', '')
        url = data.get('url', '')
        
        enabled = module_config.get("enabled", False)
        remote_url = module_config.get("remote_automation_url", "")
        
        if not enabled:
            return jsonify({
                "status": "disabled",
                "message": "Web Retriever is disabled",
                "query": query
            }), 503
        
        # Check if remote automation is configured
        if remote_url:
            # Use remote retriever on VPS
            return _remote_retrieve(query, url, remote_url)
        else:
            # Use local retriever
            return _local_retrieve(query, url)
        
    except Exception as e:
        log.error(f"Error in summarize_web: {e}")
        return jsonify({"error": str(e)}), 500

def _remote_retrieve(query, url, remote_url):
    """Retrieve via remote VPS automation"""
    try:
        import requests
        from core.config_manager import get_module_config
        
        automation_config = get_module_config("automation_hub")
        auth_token = automation_config.get("vps", {}).get("auth_token", "")
        
        payload = {
            "query": query,
            "url": url,
            "source": "web_retriever"
        }
        
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        response = requests.post(
            f"{remote_url}/web_retrieve",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "status": "error",
                "message": f"Remote retriever returned {response.status_code}",
                "fallback_to_local": True
            }), response.status_code
            
        except Exception as e:
            log.warning(f"Remote retrieve failed, falling back to local: {e}")
            return _local_retrieve(query, url)

def _local_retrieve(query, url):
    """Local web retrieval using DuckDuckGo/SerpAPI + newspaper3k"""
    try:
        import requests
        from bs4 import BeautifulSoup
        try:
            from newspaper import Article
        except ImportError:
            Article = None
        
        # If URL provided, fetch and summarize
        if url:
            try:
                response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                response.raise_for_status()
                
                # Try newspaper3k first
                if Article:
                    article = Article(url)
                    article.download()
                    article.parse()
                    text = article.text
                else:
                    # Fallback to BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text(separator=' ', strip=True)
                
                # Summarize with local LLM
                summary = _summarize_with_llm(text[:5000], query)
                
                return jsonify({
                    "status": "success",
                    "summary": summary,
                    "url": url,
                    "source": "local",
                    "text_length": len(text)
                })
            except Exception as e:
                log.error(f"Error fetching URL: {e}")
                return jsonify({
                    "status": "error",
                    "message": f"Failed to fetch URL: {str(e)}"
                }), 500
        
        # If query provided, search web
        if query:
            # Try DuckDuckGo search
            try:
                from duckduckgo_search import DDGS
                
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=3))
                
                # Summarize top results
                combined_text = "\n\n".join([r.get("body", "") for r in results[:3]])
                
                summary = _summarize_with_llm(combined_text[:5000], query)
                
                return jsonify({
                    "status": "success",
                    "summary": summary,
                    "query": query,
                    "sources": [r.get("href", "") for r in results[:3]],
                    "source": "local_ddg"
                })
                
            except ImportError:
                log.warning("duckduckgo_search not available")
                # Fallback: use simple web search API
                return jsonify({
                    "status": "partial",
                    "message": "Web search not fully configured. Install duckduckgo-search for full functionality.",
                    "query": query,
                    "summary": f"Query: {query} (Please configure web search for full results)"
                })
        
        return jsonify({
            "status": "error",
            "message": "Either query or url must be provided"
        }), 400
        
    except Exception as e:
        log.error(f"Error in local retrieve: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def _summarize_with_llm(text, query):
    """Summarize text using local LLM"""
    try:
        from local_engines.engine_manager import get_engine_manager
        
        prompt = f"""Summarize the following text in response to this query: {query}

TEXT:
{text}

Provide a concise summary with key points."""

        engine = get_engine_manager()
        summary = engine.call_llm(prompt, model="llama3.2")
        
        return summary if summary else "Failed to generate summary"
        
    except Exception as e:
        log.error(f"Error summarizing with LLM: {e}")
        return text[:500] + "..." if len(text) > 500 else text

if __name__ == '__main__':
    port = module_config.get('api', {}).get('port', 5002)
    host = suite_config.get("security", {}).get("bind_localhost_only", True)
    host_addr = "127.0.0.1" if host else "0.0.0.0"
    
    log.info(f"Starting Web Retriever API on {host_addr}:{port}")
    log.info(f"Web search available: {WEB_SEARCH_AVAILABLE}")
    log.info("Endpoints: /search, /scrape, /summarize_web, /health")
    
    app.run(host=host_addr, port=port, debug=False)

