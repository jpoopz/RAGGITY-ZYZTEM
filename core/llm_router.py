"""
Dynamic LLM Router Client
Routes LLM requests through n8n Dynamic LLM Router
Automatically falls back to local Ollama if router unavailable
Version: 7.9.6-Julian-n8nIntegration
"""

import os
import sys
import json
import requests
from typing import Dict, Optional, List
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
    from core.event_bus import publish_event
except ImportError:
    def log(msg, category="LLM_ROUTER"):
        print(f"[{category}] {msg}")
    def publish_event(event_type, sender, data=None):
        pass

class LLMRouter:
    """Dynamic LLM Router Client"""
    
    def __init__(self):
        self.base_dir = BASE_DIR
        self.config_file = os.path.join(self.base_dir, "config", "n8n_config.json")
        self.config = self._load_config()
        self.router_url = None
        self.fallback_active = False
        self.consecutive_failures = 0
        self.usage_log = os.path.join(self.base_dir, "Logs", "llm_usage.log")
        os.makedirs(os.path.dirname(self.usage_log), exist_ok=True)
        
        # Load router URL from config
        if self.config:
            self.router_url = self.config.get("llm_router") or \
                            (self.config.get("url", "") + "/webhook/llm-route" if self.config.get("url") else None)
    
    def _load_config(self) -> Dict:
        """Load n8n configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config
        except Exception as e:
            log(f"Error loading n8n config: {e}", "LLM_ROUTER", level="WARNING")
        
        return {}
    
    def _check_local_ollama(self) -> bool:
        """Check if local Ollama is available"""
        try:
            response = requests.get("http://127.0.0.1:11434/api/health", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def _call_local_ollama(self, messages: List[Dict], model: str = "llama3.2") -> Optional[Dict]:
        """Call local Ollama directly"""
        try:
            payload = {
                "model": model,
                "messages": messages
            }
            
            response = requests.post(
                "http://127.0.0.1:11434/api/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "provider": "local",
                    "content": data.get("message", {}).get("content", ""),
                    "tokens": data.get("eval_count", 0),
                    "cost": 0.0
                }
        except Exception as e:
            log(f"Local Ollama call failed: {e}", "LLM_ROUTER", level="WARNING")
        
        return None
    
    def _call_router(self, messages: List[Dict]) -> Optional[Dict]:
        """Call n8n LLM Router"""
        if not self.router_url:
            return None
        
        try:
            payload = {
                "messages": messages
            }
            
            # Get auth from config
            headers = {"Content-Type": "application/json"}
            if self.config.get("auth_user") and self.config.get("auth_pass"):
                import base64
                auth_string = f"{self.config['auth_user']}:{self.config['auth_pass']}"
                auth_bytes = auth_string.encode('utf-8')
                auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
                headers["Authorization"] = f"Basic {auth_b64}"
            
            response = requests.post(
                self.router_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.consecutive_failures = 0
                
                # Log usage
                self._log_usage(result.get("provider", "unknown"), 
                              result.get("tokens", 0),
                              result.get("cost", 0))
                
                return result
            else:
                log(f"Router returned status {response.status_code}", "LLM_ROUTER", level="WARNING")
                self.consecutive_failures += 1
        
        except Exception as e:
            log(f"Router call failed: {e}", "LLM_ROUTER", level="WARNING")
            self.consecutive_failures += 1
        
        return None
    
    def _log_usage(self, provider: str, tokens: int, cost: float):
        """Log LLM usage"""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = f"{timestamp} | {provider} | {tokens} | {cost}\n"
            
            with open(self.usage_log, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except (OSError, IOError) as e:
            log(f"Failed to write usage log: {e}", "LLM_ROUTER")
    
    def _check_fallback_status(self):
        """Check and update fallback status"""
        if self.consecutive_failures >= 3 and not self.fallback_active:
            self.fallback_active = True
            publish_event("llm_fallback_active", "llm_router", {"active": True})
            log("LLM fallback activated - local checks disabled for 5 minutes", "LLM_ROUTER")
        
        # Check if local is back online
        if self.fallback_active and self._check_local_ollama():
            # Wait a bit before re-enabling
            import time
            time.sleep(1)
            if self._check_local_ollama():
                self.fallback_active = False
                publish_event("llm_fallback_active", "llm_router", {"active": False})
                log("LLM fallback deactivated - local Ollama restored", "LLM_ROUTER")
    
    def route(self, messages: List[Dict], model: str = "llama3.2") -> Dict:
        """
        Route LLM request through Dynamic Router
        
        Args:
            messages: List of message dicts (OpenAI format)
            model: Model name (default: llama3.2)
        
        Returns:
            Dict with provider, content, tokens, cost
        """
        # Check fallback status
        self._check_fallback_status()
        
        # Try router first (if not in fallback mode)
        if not self.fallback_active and self.router_url:
            result = self._call_router(messages)
            if result:
                return result
        
        # Fallback to local Ollama
        if self._check_local_ollama():
            result = self._call_local_ollama(messages, model)
            if result:
                self._log_usage(result["provider"], result["tokens"], result["cost"])
                return result
        
        # All options failed
        return {
            "provider": "error",
            "content": "No LLM service available",
            "tokens": 0,
            "cost": 0.0,
            "error": "All LLM services unavailable"
        }
    
    def get_status(self) -> Dict:
        """Get current LLM router status"""
        local_available = self._check_local_ollama()
        router_available = self.router_url is not None
        
        if local_available:
            status = "local"
            status_text = "🟢 Local LLM (Ollama active)"
        elif router_available and not self.fallback_active:
            status = "router"
            status_text = "🟡 Router Active (cloud fallback available)"
        elif self.fallback_active:
            status = "fallback"
            status_text = "🟠 Cloud Fallback Active"
        else:
            status = "offline"
            status_text = "🔴 Offline (no LLM available)"
        
        return {
            "status": status,
            "status_text": status_text,
            "local_available": local_available,
            "router_available": router_available,
            "fallback_active": self.fallback_active,
            "consecutive_failures": self.consecutive_failures
        }

# Global instance
_llm_router_instance = None

def get_llm_router() -> LLMRouter:
    """Get global LLM router instance"""
    global _llm_router_instance
    if _llm_router_instance is None:
        _llm_router_instance = LLMRouter()
    return _llm_router_instance




