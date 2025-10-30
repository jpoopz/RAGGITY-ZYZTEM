"""
Cloud Bridge Client - Secure synchronization between local and VPS
Handles bi-directional context sync, remote execution, and encrypted transport
"""

import os
import sys
import json
import gzip
import hashlib
import requests
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log, log_exception
except ImportError:
    def log(msg, category="CLOUD"):
        print(f"[{category}] {msg}")
    def log_exception(category="ERROR", exception=None, context=""):
        print(f"[{category}] {context}: {exception}")

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    log("cryptography not available, encryption disabled", "CLOUD", level="WARNING")

class CloudBridge:
    """Manages secure synchronization with VPS"""
    
    def __init__(self):
        self.config = self._load_config()
        self.enabled = self.config.get("enabled", False)
        self.vps_url = self.config.get("vps_url", "")
        self.api_token = self.config.get("api_token", "")
        self.sync_interval = self.config.get("sync_interval", 900)  # 15 minutes
        self.last_sync_time = None
        self.last_latency_ms = None
        self.connected = False
        
        # Encryption keys
        self.rsa_public_key = None
        self.rsa_private_key = None
        self.aes_key = None
        self._load_keys()
        
        # Auto-sync thread
        self.auto_sync_enabled = self.config.get("auto_sync", False)
        self.sync_thread = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        if self.enabled and self.auto_sync_enabled:
            self.start_auto_sync()
    
    def _load_config(self) -> dict:
        """Load VPS configuration (with decryption)"""
        try:
            config_path = os.path.join(BASE_DIR, "config", "vps_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Decrypt sensitive values
                try:
                    from core.config_encrypt import get_config_encryptor
                    encryptor = get_config_encryptor()
                    config = encryptor.decrypt_config(config, ['api_token', 'auth_token'])
                except:
                    pass  # Continue with plaintext if decryption fails
                
                return config
        except Exception as e:
            log(f"Error loading VPS config: {e}", "CLOUD", level="ERROR")
        
        return {
            "enabled": False,
            "vps_url": "",
            "api_token": "",
            "sync_interval": 900,
            "auto_sync": False
        }
    
    def _load_keys(self):
        """Load RSA and AES keys"""
        try:
            keys_dir = os.path.join(BASE_DIR, "remote", "keys")
            
            # RSA Public Key
            public_key_path = os.path.join(keys_dir, "public.pem")
            if os.path.exists(public_key_path) and ENCRYPTION_AVAILABLE:
                with open(public_key_path, 'rb') as f:
                    self.rsa_public_key = serialization.load_pem_public_key(f.read())
            
            # RSA Private Key
            private_key_path = os.path.join(keys_dir, "private.pem")
            if os.path.exists(private_key_path) and ENCRYPTION_AVAILABLE:
                with open(private_key_path, 'rb') as f:
                    self.rsa_private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None
                    )
            
            # AES Key (shared secret)
            aes_key_path = os.path.join(keys_dir, "aes.key")
            if os.path.exists(aes_key_path) and ENCRYPTION_AVAILABLE:
                with open(aes_key_path, 'rb') as f:
                    self.aes_key = f.read()
            elif ENCRYPTION_AVAILABLE:
                # Generate and save
                self.aes_key = Fernet.generate_key()
                os.makedirs(keys_dir, exist_ok=True)
                with open(aes_key_path, 'wb') as f:
                    f.write(self.aes_key)
                
        except Exception as e:
            log(f"Error loading encryption keys: {e}", "CLOUD", level="WARNING")
    
    def encrypt_payload(self, data: dict) -> bytes:
        """Encrypt payload using AES"""
        if not ENCRYPTION_AVAILABLE or not self.aes_key:
            return json.dumps(data).encode('utf-8')
        
        try:
            fernet = Fernet(self.aes_key)
            return fernet.encrypt(json.dumps(data).encode('utf-8'))
        except Exception as e:
            log(f"Encryption error: {e}", "CLOUD", level="ERROR")
            return json.dumps(data).encode('utf-8')
    
    def decrypt_payload(self, encrypted_data: bytes) -> dict:
        """Decrypt payload using AES"""
        if not ENCRYPTION_AVAILABLE or not self.aes_key:
            try:
                return json.loads(encrypted_data.decode('utf-8'))
            except:
                return {}
        
        try:
            fernet = Fernet(self.aes_key)
            decrypted = fernet.decrypt(encrypted_data)
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            log(f"Decryption error: {e}", "CLOUD", level="ERROR")
            return {}
    
    def verify_health(self) -> bool:
        """Ping VPS and check connection with retry logic"""
        try:
            if not self.vps_url:
                self.connected = False
                return False
            
            # TLS verification (from config)
            verify_tls = self.config.get("verify_tls", True)
            
            start_time = time.time()
            response = requests.get(
                f"{self.vps_url}/ping",
                timeout=5,
                verify=verify_tls  # TLS certificate verification
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                self.connected = True
                self.last_latency_ms = elapsed_ms
                self.reconnect_attempts = 0  # Reset on success
                log(f"VPS health check OK ({elapsed_ms}ms)", "CLOUD")
                return True
            else:
                self.connected = False
                self.reconnect_attempts += 1
                log(f"VPS health check failed: {response.status_code}", "CLOUD", level="WARNING")
                return False
                
        except Exception as e:
            self.connected = False
            self.reconnect_attempts += 1
            log(f"VPS health check error: {e}", "CLOUD", level="WARNING")
            return False
    
    def reconnect_with_backoff(self) -> bool:
        """Reconnect to VPS with exponential backoff"""
        retry_interval = min(10 * (2 ** min(self.reconnect_attempts, 4)), 120)  # Max 2 minutes
        
        log(f"Attempting to reconnect (attempt {self.reconnect_attempts + 1})...", "CLOUD")
        time.sleep(retry_interval)
        
        return self.verify_health()
    
    def sync_context(self) -> bool:
        """
        Push local context bundle to VPS with reconnect logic
        """
        try:
            if not self.enabled or not self.vps_url:
                return False
            
            # Verify health first
            if not self.connected:
                if not self.verify_health():
                    # Try to reconnect
                    if not self.reconnect_with_backoff():
                        log("Cannot sync: VPS unreachable", "CLOUD", level="WARNING")
                        return False
            
            # Build local context
            from core.context_graph import get_context_graph
            from core.memory_manager import get_memory_manager
            
            graph = get_context_graph(user="julian")
            context = graph.build_context(include_rag=False)  # Don't include RAG for sync
            
            # Compress if large
            context_json = json.dumps(context)
            if len(context_json.encode('utf-8')) > 2 * 1024 * 1024:  # > 2MB
                compressed = gzip.compress(context_json.encode('utf-8'))
                context_json = compressed
            
            # Encrypt if enabled
            encrypted = False
            payload_data = context_json
            if ENCRYPTION_AVAILABLE and self.aes_key:
                encrypted = True
                payload_data = self.encrypt_payload(context)
            
            # Send to VPS
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            
            payload = {
                "context_json": context_json.decode('utf-8') if isinstance(context_json, bytes) else context_json,
                "timestamp": datetime.now().isoformat(),
                "user": "julian"
            }
            
            # TLS verification (from config)
            verify_tls = self.config.get("verify_tls", True)
            
            response = requests.post(
                f"{self.vps_url}/context/push",
                json=payload,
                headers=headers,
                timeout=30,
                verify=verify_tls  # TLS certificate verification
            )
            
            if response.status_code == 200:
                self.last_sync_time = datetime.now()
                sync_time_str = self.last_sync_time.strftime("%H:%M:%S")
                log(f"☁ Synced successfully at {sync_time_str}", "CLOUD")
                return True
            else:
                log(f"Context sync failed: {response.status_code}", "CLOUD", level="ERROR")
                self.connected = False
                return False
                
        except Exception as e:
            log_exception("CLOUD", e, "Error syncing context")
            self.connected = False
            return False
    
    def fetch_remote_context(self) -> Optional[Dict[str, Any]]:
        """
        Pull latest VPS context bundle
        """
        try:
            if not self.enabled or not self.vps_url:
                return None
            
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            
            # TLS verification (from config)
            verify_tls = self.config.get("verify_tls", True)
            
            response = requests.get(
                f"{self.vps_url}/context/pull",
                params={"user": "julian"},
                headers=headers,
                timeout=10,
                verify=verify_tls  # TLS certificate verification
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    remote_context = data.get("context")
                    log("Remote context fetched from VPS", "CLOUD")
                    return remote_context
                else:
                    log("No remote context available", "CLOUD")
                    return None
            else:
                log(f"Failed to fetch remote context: {response.status_code}", "CLOUD", level="ERROR")
                return None
                
        except Exception as e:
            log_exception("CLOUD", e, "Error fetching remote context")
            return None
    
    def remote_execute(self, task: str, params: dict) -> Optional[Dict[str, Any]]:
        """
        Offload task to VPS for execution
        """
        try:
            if not self.enabled or not self.vps_url:
                return None
            
            # Encrypt params if enabled
            encrypted = False
            payload_str = ""
            if ENCRYPTION_AVAILABLE and self.aes_key:
                encrypted = True
                encrypted_bytes = self.encrypt_payload(params)
                payload_str = encrypted_bytes.decode('latin-1')  # Base64-safe encoding
            
            request_data = {
                "task": task,
                "params": params if not encrypted else {},
                "encrypted": encrypted,
                "payload": payload_str
            }
            
            headers = {}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            
            response = requests.post(
                f"{self.vps_url}/execute",
                json=request_data,
                headers=headers,
                timeout=120  # Long timeout for remote execution
            )
            
            if response.status_code == 200:
                result = response.json()
                log(f"Remote task '{task}' executed successfully", "CLOUD")
                return result.get("result")
            else:
                log(f"Remote task '{task}' failed: {response.status_code}", "CLOUD", level="ERROR")
                return None
                
        except Exception as e:
            log_exception("CLOUD", e, f"Error executing remote task '{task}'")
            return None
    
    def start_auto_sync(self):
        """Start background auto-sync thread"""
        if self.running:
            return
        
        self.running = True
        
        def sync_loop():
            consecutive_errors = 0
            adaptive_sleep = self.sync_interval
            
            while self.running:
                try:
                    if self.enabled and self.auto_sync_enabled:
                        # Verify health with reconnect logic
                        if not self.connected:
                            if not self.reconnect_with_backoff():
                                consecutive_errors += 1
                                adaptive_sleep = min(adaptive_sleep * 1.5, 1800)  # Max 30 min
                                time.sleep(adaptive_sleep)
                                continue
                        
                        # Sync if connected
                        if self.connected:
                            success = self.sync_context()
                            if success:
                                consecutive_errors = 0
                                adaptive_sleep = self.sync_interval  # Reset to normal
                            else:
                                consecutive_errors += 1
                                adaptive_sleep = min(adaptive_sleep * 1.2, 900)  # Max 15 min
                    else:
                        # Not enabled, sleep normally
                        adaptive_sleep = self.sync_interval
                    
                    time.sleep(adaptive_sleep)
                except Exception as e:
                    log(f"Error in auto-sync loop: {e}", "CLOUD", level="ERROR")
                    consecutive_errors += 1
                    adaptive_sleep = min(adaptive_sleep * 1.5, 1800)
                    time.sleep(min(adaptive_sleep, 300))  # Max 5 min wait on error
        
        self.sync_thread = threading.Thread(target=sync_loop, daemon=True)
        self.sync_thread.start()
        log(f"Auto-sync started (interval: {self.sync_interval}s)", "CLOUD")
    
    def stop_auto_sync(self):
        """Stop background auto-sync gracefully"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for thread to finish (with timeout)
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
            if self.sync_thread.is_alive():
                log("Auto-sync thread did not terminate cleanly", "CLOUD", level="WARNING")
        
        log("Auto-sync stopped", "CLOUD")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bridge status"""
        return {
            "enabled": self.enabled,
            "connected": self.connected,
            "vps_url": self.vps_url,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "last_latency_ms": self.last_latency_ms,
            "auto_sync_enabled": self.auto_sync_enabled,
            "sync_interval": self.sync_interval,
            "encryption_available": ENCRYPTION_AVAILABLE
        }

# Global cloud bridge instance
_cloud_bridge_instance = None

def get_cloud_bridge():
    """Get global cloud bridge (singleton)"""
    global _cloud_bridge_instance
    if _cloud_bridge_instance is None:
        _cloud_bridge_instance = CloudBridge()
    return _cloud_bridge_instance

