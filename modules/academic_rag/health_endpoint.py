"""
Unified Health Endpoint for Dashboard Polling

Provides comprehensive system health status in a single JSON response.
Designed for UI polling (recommended: 10s interval).
"""

import os
import sys
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

def get_full_health() -> dict:
    """
    Get comprehensive system health status.
    
    Returns:
        dict: Full health status including API, CLO, vector store, Ollama, system resources
    """
    health = {
        "timestamp": None,
        "api": {"ok": False},
        "clo": {"ok": False},
        "vector_store": "unknown",
        "ollama": {"ok": False},
        "sys": {}
    }
    
    try:
        from datetime import datetime
        health["timestamp"] = datetime.now().isoformat()
    except Exception:
        pass
    
    # API Health
    try:
        from core.config_manager import get_module_config
        api_config = get_module_config("academic_rag")
        api_host = api_config.get("api", {}).get("host", "127.0.0.1")
        api_port = int(api_config.get("api", {}).get("port", 5000))
        
        health["api"]["host"] = api_host
        health["api"]["port"] = api_port
        
        # Check if API is responding
        import requests
        try:
            r = requests.get(f"http://{api_host}:{api_port}/health", timeout=1.5)
            health["api"]["ok"] = r.ok
        except Exception:
            health["api"]["ok"] = False
    except Exception as e:
        health["api"]["error"] = str(e)
    
    # CLO Bridge Health
    try:
        from modules.clo_companion.config import CLO_HOST, CLO_PORT
        health["clo"]["host"] = CLO_HOST
        health["clo"]["port"] = CLO_PORT
        
        # TCP probe with handshake
        import socket
        import json
        try:
            with socket.create_connection((CLO_HOST, CLO_PORT), timeout=0.8) as sock:
                sock.settimeout(0.8)
                # Send ping
                ping = json.dumps({"ping": "clo"}) + "\n"
                sock.sendall(ping.encode('utf-8'))
                # Read response
                response = sock.recv(1024).decode('utf-8').strip()
                data = json.loads(response)
                if data.get("pong") == "clo":
                    health["clo"]["ok"] = True
                    health["clo"]["handshake"] = "ok"
                else:
                    health["clo"]["ok"] = False
                    health["clo"]["handshake"] = "wrong_service"
        except json.JSONDecodeError:
            health["clo"]["ok"] = False
            health["clo"]["handshake"] = "invalid_protocol"
        except socket.timeout:
            health["clo"]["ok"] = False
            health["clo"]["handshake"] = "timeout"
        except Exception as e:
            health["clo"]["ok"] = False
            health["clo"]["error"] = e.__class__.__name__
    except Exception:
        health["clo"]["host"] = "127.0.0.1"
        health["clo"]["port"] = 51235
        health["clo"]["ok"] = False
    
    # Vector Store
    try:
        from core.settings import load_settings
        settings = load_settings()
        health["vector_store"] = settings.vector_store
    except Exception:
        health["vector_store"] = "unknown"
    
    # Ollama Health
    try:
        from core.llm_connector import ollama_ok, model_present
        from core.settings import load_settings
        settings = load_settings()
        
        health["ollama"]["ok"] = ollama_ok()
        health["ollama"]["model"] = settings.model_name
        health["ollama"]["model_ok"] = model_present(settings.model_name) if health["ollama"]["ok"] else False
    except Exception as e:
        health["ollama"]["error"] = str(e)
    
    # System Resources
    try:
        # Disk space
        vector_dir = os.path.join(BASE_DIR, "vector_store")
        if os.path.exists(vector_dir):
            free_bytes = shutil.disk_usage(vector_dir).free
            health["sys"]["disk_free_gb"] = round(free_bytes / (1024**3), 1)
        
        # RAM
        if PSUTIL_AVAILABLE:
            ram_bytes = psutil.virtual_memory().available
            health["sys"]["ram_free_gb"] = round(ram_bytes / (1024**3), 1)
        
        # Python version
        health["sys"]["py"] = f"{sys.version_info.major}.{sys.version_info.minor}"
    except Exception as e:
        health["sys"]["error"] = str(e)
    
    return health


def get_clo_health() -> dict:
    """
    Get CLO Bridge health only (lightweight for frequent polling).
    
    Returns:
        dict: CLO health status
    """
    try:
        from modules.clo_companion.config import CLO_HOST, CLO_PORT
        import socket
        import json
        
        try:
            with socket.create_connection((CLO_HOST, CLO_PORT), timeout=0.8) as sock:
                sock.settimeout(0.8)
                ping = json.dumps({"ping": "clo"}) + "\n"
                sock.sendall(ping.encode('utf-8'))
                response = sock.recv(1024).decode('utf-8').strip()
                data = json.loads(response)
                
                if data.get("pong") == "clo":
                    return {
                        "ok": True,
                        "host": CLO_HOST,
                        "port": CLO_PORT,
                        "handshake": "ok"
                    }
                else:
                    return {
                        "ok": False,
                        "host": CLO_HOST,
                        "port": CLO_PORT,
                        "handshake": "wrong_service",
                        "detail": str(data)
                    }
        except Exception as e:
            return {
                "ok": False,
                "host": CLO_HOST,
                "port": CLO_PORT,
                "error": e.__class__.__name__
            }
    except Exception:
        return {
            "ok": False,
            "host": "127.0.0.1",
            "port": 51235,
            "error": "config_unavailable"
        }

