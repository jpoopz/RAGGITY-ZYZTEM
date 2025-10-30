"""
Cloud Bridge Client
Provides authenticated communication with remote VPS/cloud services
Supports events, backups, and retry logic
"""

from __future__ import annotations

import os
import requests
import time
import json
import base64
import hashlib
from typing import Any, Dict

from logger import get_logger
from .config import CFG

log = get_logger("bridge")


class CloudBridge:
    """Client for cloud/VPS API communication"""
    
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or os.getenv("CLOUD_URL", "https://your-vps-domain/api")
        self.api_key = api_key or os.getenv("CLOUD_KEY", "")
        
        # Setup session with headers
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "RAGGITY-CLIENT"})
        
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
        
        log.info(f"CloudBridge initialized: {self.base_url}")

    def _req(self, method: str, path: str, **kw) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            **kw: Additional keyword arguments for requests
            
        Returns:
            JSON response as dictionary
            
        Raises:
            RuntimeError: If all retries fail
        """
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        
        for attempt in range(3):
            try:
                log.info(f"[Bridge] {method} {url} (attempt {attempt + 1}/3)")
                
                r = self.session.request(method, url, timeout=15, **kw)
                r.raise_for_status()
                
                log.info(f"[Bridge] {method} {url} success")
                return r.json()
                
            except requests.exceptions.HTTPError as e:
                log.error(f"[Bridge] HTTP error {e.response.status_code}: {url}")
                if e.response.status_code in [401, 403, 404]:
                    # Don't retry auth/not found errors
                    raise
                log.warning(f"[Bridge] Retry {attempt + 1}/3 after HTTP error")
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.Timeout:
                log.warning(f"[Bridge] Timeout on {url}; retry {attempt + 1}/3")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.ConnectionError as e:
                log.warning(f"[Bridge] Connection error: {e}; retry {attempt + 1}/3")
                time.sleep(2 ** attempt)
                
            except Exception as e:
                log.error(f"[Bridge] Unexpected error: {e}")
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        
        raise RuntimeError(f"Bridge call failed after 3 attempts: {url}")

    def health(self) -> Dict[str, Any]:
        """
        Check cloud service health
        
        Returns:
            Health status dictionary
        """
        return self._req("GET", "health")

    def send_event(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send event to cloud service
        
        Args:
            name: Event name
            payload: Event data
            
        Returns:
            Response from server
        """
        data = {
            "event": name,
            "payload": payload,
            "ts": time.time(),
            "signature": self._sign(json.dumps(payload, sort_keys=True))
        }
        
        log.info(f"[Bridge] Sending event: {name}")
        return self._req("POST", "events", json=data)

    def push_vector_backup(self, vector_path: str) -> Dict[str, Any]:
        """
        Upload local FAISS index or data chunk to remote for backup
        
        Args:
            vector_path: Path to vector file to backup
            
        Returns:
            Backup confirmation
            
        Raises:
            FileNotFoundError: If vector_path doesn't exist
        """
        if not os.path.exists(vector_path):
            log.error(f"[Bridge] Vector file not found: {vector_path}")
            raise FileNotFoundError(vector_path)
        
        log.info(f"[Bridge] Reading vector file: {vector_path}")
        
        # Read and encode file
        with open(vector_path, "rb") as f:
            data_bytes = f.read()
        
        # Base64 encode for JSON transport
        b64_data = base64.b64encode(data_bytes).decode()
        
        log.info(f"[Bridge] Encoded {len(data_bytes)} bytes -> {len(b64_data)} chars")
        
        payload = {
            "file": os.path.basename(vector_path),
            "data": b64_data,
            "size": len(data_bytes),
            "checksum": hashlib.md5(data_bytes).hexdigest()
        }
        
        log.info(f"[Bridge] Uploading backup: {os.path.basename(vector_path)}")
        result = self._req("POST", "backup/vector", json=payload)
        
        log.info(f"[Bridge] Backup complete: {os.path.basename(vector_path)}")
        return result

    def pull_vector_backup(self, filename: str, destination: str) -> bool:
        """
        Download vector backup from cloud
        
        Args:
            filename: Name of backup file
            destination: Local path to save
            
        Returns:
            True if successful
        """
        try:
            log.info(f"[Bridge] Downloading backup: {filename}")
            
            result = self._req("GET", f"backup/vector/{filename}")
            
            # Decode base64 data
            b64_data = result.get("data", "")
            data_bytes = base64.b64decode(b64_data)
            
            # Verify checksum if provided
            if "checksum" in result:
                local_checksum = hashlib.md5(data_bytes).hexdigest()
                if local_checksum != result["checksum"]:
                    log.error("[Bridge] Checksum mismatch on download")
                    return False
            
            # Write to file
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            with open(destination, "wb") as f:
                f.write(data_bytes)
            
            log.info(f"[Bridge] Downloaded {len(data_bytes)} bytes to {destination}")
            return True
            
        except Exception as e:
            log.error(f"[Bridge] Download failed: {e}")
            return False

    def _sign(self, msg: str) -> str:
        """
        Sign message with API key for verification
        
        Args:
            msg: Message to sign
            
        Returns:
            SHA256 signature hex string
        """
        secret = self.api_key or "local"
        signature = hashlib.sha256((secret + msg).encode()).hexdigest()
        return signature


# Global bridge instance
bridge = CloudBridge()
