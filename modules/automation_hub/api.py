"""
Automation Hub Module - Flask API Server (STUB)
"""

import sys
import os

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# Add paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="AUTOMATION"):
        print(f"[{category}] {msg}")

from core.config_manager import get_module_config, get_suite_config, get_auth_token
from core.auth_helper import require_auth_token

app = Flask(__name__)

suite_config = get_suite_config()
if suite_config.get("security", {}).get("cors_enabled", False):
    CORS(app)

module_config = get_module_config("automation_hub")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "module_id": "automation_hub",
        "version": "1.0.0",
        "uptime_seconds": 0,
        "enabled": module_config.get("enabled", False)
    })

@app.route('/sync_backup', methods=['POST'])
@require_auth_token
def sync_backup():
    """Sync vault backup to VPS (nightly task)"""
    try:
        from core.config_manager import get_suite_config
        
        suite_config = get_suite_config()
        vault_path = suite_config.get("user_profile", {}).get("obsidian_vault_path", "")
        
        if not vault_path or not os.path.exists(vault_path):
            return jsonify({
                "status": "error",
                "message": "Vault path not configured or not found"
            }), 400
        
        # Create backup archive
        import tarfile
        import tempfile
        from datetime import datetime
        
        backup_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz')
        backup_file.close()
        
        log(f"Creating backup: {backup_file.name}", "AUTOMATION")
        
        with tarfile.open(backup_file.name, "w:gz") as tar:
            tar.add(vault_path, arcname="vault_backup")
        
        # Send to VPS if configured
        vps_url = module_config.get("vps", {}).get("remote_automation_url", "")
        if vps_url:
            return _send_to_vps_backup(backup_file.name, vps_url)
        else:
            # Local backup only
            backup_dir = os.path.join(BASE_DIR, "Backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_backup = os.path.join(backup_dir, f"vault_backup_{timestamp}.tar.gz")
            os.rename(backup_file.name, final_backup)
            
            return jsonify({
                "status": "success",
                "backup_file": final_backup,
                "message": "Backup created locally (VPS not configured)"
            })
        
    except Exception as e:
        log(f"Error in sync_backup: {e}", "AUTOMATION", level="ERROR")
        return jsonify({"error": str(e)}), 500

def _send_to_vps_backup(backup_file, vps_url):
    """Send backup to VPS"""
    try:
        import requests
        
        auth_token = module_config.get("vps", {}).get("auth_token", "")
        
        with open(backup_file, 'rb') as f:
            files = {'backup': f}
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            response = requests.post(
                f"{vps_url}/sync_backup",
                files=files,
                headers=headers,
                timeout=300
            )
        
        os.remove(backup_file)
        
        if response.status_code == 200:
            return jsonify({
                "status": "success",
                "message": "Backup synced to VPS",
                "vps_response": response.json()
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"VPS sync failed: {response.status_code}"
            }), response.status_code
            
    except Exception as e:
        log(f"Error sending to VPS: {e}", "AUTOMATION", level="ERROR")
        return jsonify({
            "status": "error",
            "message": f"Failed to send to VPS: {str(e)}"
        }), 500

@app.route('/web_retrieve', methods=['POST'])
@require_auth_token
def web_retrieve():
    """Proxy web retrieval to Web Retriever module"""
    try:
        data = request.json or {}
        query = data.get('query', '')
        url = data.get('url', '')
        
        # Call Web Retriever module
        from core.module_registry import get_registry
        
        registry = get_registry()
        web_module = registry.get_module("web_retriever")
        
        if not web_module:
            return jsonify({
                "status": "error",
                "message": "Web Retriever module not available"
            }), 503
        
        port = web_module.get('port', 5002)
        
        # Forward request
        import requests
        response = requests.post(
            f"http://127.0.0.1:{port}/summarize_web",
            json={"query": query, "url": url},
            headers={"Authorization": f"Bearer {get_auth_token()}"},
            timeout=30
        )
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        log(f"Error in web_retrieve: {e}", "AUTOMATION", level="ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    """Health check for VPS connectivity"""
    try:
        vps_url = module_config.get("vps", {}).get("remote_automation_url", "")
        
        if not vps_url:
            return jsonify({
                "status": "ok",
                "vps_configured": False,
                "message": "VPS not configured"
            })
        
        # Ping VPS
        import requests
        import time
        
        start_time = time.time()
        try:
            response = requests.get(
                f"{vps_url}/ping",
                timeout=5
            )
            latency_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                return jsonify({
                    "status": "ok",
                    "vps_configured": True,
                    "vps_online": True,
                    "latency_ms": latency_ms,
                    "vps_response": response.json()
                })
            else:
                return jsonify({
                    "status": "warning",
                    "vps_configured": True,
                    "vps_online": False,
                    "message": f"VPS returned {response.status_code}"
                })
        except requests.exceptions.RequestException as e:
            return jsonify({
                "status": "error",
                "vps_configured": True,
                "vps_online": False,
                "message": str(e)
            })
        
    except Exception as e:
        log(f"Error in ping: {e}", "AUTOMATION", level="ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/test_webhook', methods=['POST'])
@require_auth_token
def test_webhook():
    """Test n8n webhook (STUB)"""
    try:
        data = request.json or {}
        webhook_url = data.get('webhook_url') or module_config.get('n8n', {}).get('webhook_url', '')
        
        if not webhook_url:
            return jsonify({
                "status": "error",
                "message": "No webhook URL configured. Set in module config."
            }), 400
        
        # Test webhook with dummy payload
        test_payload = {
            "source": "automation_hub",
            "action": "test",
            "timestamp": "2025-10-29T18:00:00"
        }
        
        try:
            response = requests.post(
                webhook_url,
                json=test_payload,
                timeout=10,
                headers={
                    "Authorization": f"Bearer {module_config.get('n8n', {}).get('token', '')}"
                } if module_config.get('n8n', {}).get('token') else {}
            )
            
            return jsonify({
                "status": "success",
                "webhook_url": webhook_url,
                "response_status": response.status_code,
                "response_text": response.text[:200]
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Webhook request failed: {str(e)}"
            }), 500
        
    except Exception as e:
        log(f"Error in test_webhook: {e}", "AUTOMATION")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = module_config.get('api', {}).get('port', 5003)
    host = suite_config.get("security", {}).get("bind_localhost_only", True)
    host_addr = "127.0.0.1" if host else "0.0.0.0"
    
    log(f"Starting Automation Hub API on {host_addr}:{port}", "AUTOMATION")
    app.run(host=host_addr, port=port, debug=False)

