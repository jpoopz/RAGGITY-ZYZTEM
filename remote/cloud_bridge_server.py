"""
Cloud Bridge Server - FastAPI server for Hostinger VPS
Handles secure context sync, remote execution, and bi-directional replication
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import gzip
import json

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

try:
    from fastapi import FastAPI, Request, HTTPException, Depends, Header
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("ERROR: fastapi and uvicorn required for Cloud Bridge server")
    print("Install with: pip install fastapi uvicorn")
    sys.exit(1)

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization
    ENCRYPTION_AVAILABLE = True
except ImportError:
    print("WARNING: cryptography not available, encryption disabled")
    ENCRYPTION_AVAILABLE = False

app = FastAPI(title="Julian Assistant Cloud Bridge", version="4.0.0")

# Security
VPS_AUTH_TOKEN = os.environ.get("VPS_AUTH_TOKEN", "")
RSA_PRIVATE_KEY = None
AES_KEY = None

# Load RSA private key if available
try:
    if ENCRYPTION_AVAILABLE:
        private_key_path = os.path.join(os.path.dirname(__file__), "keys", "private.pem")
        if os.path.exists(private_key_path):
            with open(private_key_path, 'rb') as f:
                RSA_PRIVATE_KEY = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
except Exception as e:
    print(f"Warning: Could not load RSA key: {e}")

# Load or generate AES key
try:
    if ENCRYPTION_AVAILABLE:
        aes_key_path = os.path.join(os.path.dirname(__file__), "keys", "aes.key")
        if os.path.exists(aes_key_path):
            with open(aes_key_path, 'rb') as f:
                AES_KEY = f.read()
        else:
            AES_KEY = Fernet.generate_key()
            os.makedirs(os.path.dirname(aes_key_path), exist_ok=True)
            with open(aes_key_path, 'wb') as f:
                f.write(AES_KEY)
except Exception as e:
    print(f"Warning: Could not setup AES: {e}")

def verify_token(authorization: str = Header(None)):
    """Verify authorization token"""
    if not VPS_AUTH_TOKEN:
        return True  # No auth if not set
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "").strip()
    if token != VPS_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return True

def decrypt_payload(encrypted_data: bytes) -> dict:
    """Decrypt payload using AES"""
    if not ENCRYPTION_AVAILABLE or not AES_KEY:
        # Fallback: assume JSON
        try:
            return json.loads(encrypted_data.decode('utf-8'))
        except:
            return {}
    
    try:
        fernet = Fernet(AES_KEY)
        decrypted = fernet.decrypt(encrypted_data)
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        print(f"Decryption error: {e}")
        return {}

def encrypt_payload(data: dict) -> bytes:
    """Encrypt payload using AES"""
    if not ENCRYPTION_AVAILABLE or not AES_KEY:
        # Fallback: JSON
        return json.dumps(data).encode('utf-8')
    
    try:
        fernet = Fernet(AES_KEY)
        return fernet.encrypt(json.dumps(data).encode('utf-8'))
    except Exception as e:
        print(f"Encryption error: {e}")
        return json.dumps(data).encode('utf-8')

class ContextPayload(BaseModel):
    context_json: str
    timestamp: str
    user: str = "julian"

class ExecuteRequest(BaseModel):
    task: str
    params: dict
    encrypted: bool = False
    payload: str = ""

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Cloud Bridge Server",
        "version": "4.0.0",
        "encryption": ENCRYPTION_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/context/push")
async def push_context(
    request_data: ContextPayload,
    authorized: bool = Depends(verify_token)
):
    """
    Receive local context bundles from client
    """
    try:
        # Store context locally
        storage_dir = Path(os.path.expanduser("~/assistant/context_storage"))
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        context_file = storage_dir / f"context_{timestamp}.json"
        
        context_data = json.loads(request_data.context_json)
        
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, indent=2)
        
        # Compress if large
        if context_file.stat().st_size > 2 * 1024 * 1024:  # > 2MB
            compressed = storage_dir / f"context_{timestamp}.json.gz"
            with open(context_file, 'rb') as f_in:
                with gzip.open(compressed, 'wb') as f_out:
                    f_out.writelines(f_in)
            context_file.unlink()
            context_file = compressed
        
        return {
            "status": "success",
            "stored_path": str(context_file),
            "timestamp": request_data.timestamp
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/context/pull")
async def pull_context(
    user: str = "julian",
    authorized: bool = Depends(verify_token)
):
    """
    Send latest VPS context to local client
    """
    try:
        storage_dir = Path(os.path.expanduser("~/assistant/context_storage"))
        
        # Get most recent context
        contexts = sorted(
            storage_dir.glob("context_*.json*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if not contexts:
            return {
                "status": "empty",
                "context": None
            }
        
        latest = contexts[0]
        
        # Read and decompress if needed
        if latest.suffix == '.gz':
            with gzip.open(latest, 'rt', encoding='utf-8') as f:
                context_data = json.load(f)
        else:
            with open(latest, 'r', encoding='utf-8') as f:
                context_data = json.load(f)
        
        return {
            "status": "success",
            "context": context_data,
            "timestamp": datetime.fromtimestamp(latest.stat().st_mtime).isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/execute")
async def execute_task(
    request_data: ExecuteRequest,
    authorized: bool = Depends(verify_token)
):
    """
    Remote task execution (LLM query, CLO render, backup push)
    """
    try:
        # Decrypt payload if needed
        if request_data.encrypted:
            params = decrypt_payload(request_data.payload.encode('utf-8'))
        else:
            params = request_data.params
        
        task = request_data.task
        
        # Route to task handler
        if task == "rag_query":
            result = await handle_rag_query(params)
        elif task == "clo_render":
            result = await handle_clo_render(params)
        elif task == "backup_push":
            result = await handle_backup_push(params)
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": f"Unknown task: {task}"}
            )
        
        return {
            "status": "success",
            "task": task,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

async def handle_rag_query(params: dict):
    """Handle remote RAG query execution"""
    try:
        query = params.get("query", "")
        if not query:
            return {"error": "Query required"}
        
        # Run LLM query (would use local Ollama or API)
        # For now, return mock response
        return {
            "response": f"Remote LLM response for: {query}",
            "source": "vps",
            "model": "llama3.2"
        }
    except Exception as e:
        return {"error": str(e)}

async def handle_clo_render(params: dict):
    """Handle remote CLO render execution"""
    try:
        prompt = params.get("prompt", "")
        if not prompt:
            return {"error": "Prompt required"}
        
        # Run CLO render (would use GPU on VPS)
        # For now, return mock response
        return {
            "status": "rendered",
            "obj_file": f"/tmp/rendered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.obj",
            "prompt": prompt,
            "source": "vps"
        }
    except Exception as e:
        return {"error": str(e)}

async def handle_backup_push(params: dict):
    """Handle backup upload to cloud storage"""
    try:
        backup_data = params.get("backup_data", "")
        backup_name = params.get("backup_name", f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
        
        # Store backup
        backup_dir = Path(os.path.expanduser("~/assistant/backups"))
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / backup_name
        
        # Write backup (would decode from base64 in production)
        with open(backup_path, 'wb') as f:
            import base64
            f.write(base64.b64decode(backup_data))
        
        return {
            "status": "stored",
            "backup_path": str(backup_path),
            "size_mb": backup_path.stat().st_size / (1024 * 1024)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/ping")
async def ping():
    """Simple ping endpoint for latency check"""
    return {
        "status": "pong",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.environ.get("VPS_PORT", "8000"))
    host = os.environ.get("VPS_HOST", "0.0.0.0")
    
    print(f"Starting Cloud Bridge Server on {host}:{port}")
    print(f"Encryption: {'Available' if ENCRYPTION_AVAILABLE else 'Disabled'}")
    
    uvicorn.run(app, host=host, port=port)




