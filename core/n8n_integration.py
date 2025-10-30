"""
n8n Integration Module
Handles connection and communication with n8n on Hostinger VPS
Version: 7.9.5-Julian-SmartCleanup
"""

import os
import sys
import json
import requests
import base64
from typing import Dict, Optional

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="N8N"):
        print(f"[{category}] {msg}")

class N8nIntegration:
    """Handles n8n integration"""
    
    def __init__(self):
        self.base_dir = BASE_DIR
        self.config_file = os.path.join(self.base_dir, "config", "n8n_config.json")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load n8n configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config
            else:
                # Create default config
                default_config = {
                    "url": "",
                    "auth_user": "",
                    "auth_pass": "",
                    "enabled": False
                }
                self._save_config(default_config)
                return default_config
        except Exception as e:
            log(f"Error loading n8n config: {e}", "N8N", level="ERROR")
            return {"enabled": False}
    
    def _save_config(self, config: Dict):
        """Save n8n configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"Error saving n8n config: {e}", "N8N", level="ERROR")
    
    def _get_auth_header(self) -> Optional[str]:
        """Get Basic Auth header"""
        if not self.config.get("auth_user") or not self.config.get("auth_pass"):
            return None
        
        auth_string = f"{self.config['auth_user']}:{self.config['auth_pass']}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        return f"Basic {auth_b64}"
    
    def test_connection(self) -> Dict:
        """Test connection to n8n"""
        if not self.config.get("enabled"):
            return {"success": False, "message": "n8n integration is disabled"}
        
        url = self.config.get("url", "")
        if not url:
            return {"success": False, "message": "n8n URL not configured"}
        
        try:
            # Try to access n8n health endpoint or webhook
            test_url = f"{url}/webhook/julian-events"
            
            headers = {}
            auth_header = self._get_auth_header()
            if auth_header:
                headers["Authorization"] = auth_header
            
            response = requests.post(
                test_url,
                json={"test": True, "event_type": "PING"},
                headers=headers,
                timeout=5
            )
            
            if response.status_code in [200, 404]:  # 404 means n8n is reachable but endpoint may not exist yet
                return {"success": True, "message": "n8n is reachable"}
            else:
                return {"success": False, "message": f"n8n returned status {response.status_code}"}
        
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "Cannot connect to n8n - check URL and network"}
        except Exception as e:
            return {"success": False, "message": f"Error testing connection: {e}"}
    
    def send_event(self, event_type: str, sender: str, data: Dict = None) -> bool:
        """Send event to n8n webhook"""
        if not self.config.get("enabled"):
            return False
        
        url = self.config.get("url", "")
        if not url:
            return False
        
        try:
            webhook_url = f"{url}/webhook/julian-events"
            
            payload = {
                "event_type": event_type,
                "sender": sender,
                "data": data or {},
                "timestamp": __import__("datetime").datetime.now().isoformat()
            }
            
            headers = {"Content-Type": "application/json"}
            auth_header = self._get_auth_header()
            if auth_header:
                headers["Authorization"] = auth_header
            
            response = requests.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                log(f"Event sent to n8n: {event_type}", "N8N")
                return True
            else:
                log(f"n8n webhook returned {response.status_code}", "N8N", level="WARNING")
                return False
        
        except Exception as e:
            log(f"Error sending event to n8n: {e}", "N8N", level="WARNING")
            return False
    
    def update_config(self, url: str, auth_user: str, auth_pass: str, enabled: bool = True):
        """Update n8n configuration"""
        self.config = {
            "url": url,
            "auth_user": auth_user,
            "auth_pass": auth_pass,
            "enabled": enabled
        }
        self._save_config(self.config)
        log("n8n configuration updated", "N8N")

# Global instance
_n8n_instance = None

def get_n8n() -> N8nIntegration:
    """Get global n8n integration instance"""
    global _n8n_instance
    if _n8n_instance is None:
        _n8n_instance = N8nIntegration()
    return _n8n_instance




