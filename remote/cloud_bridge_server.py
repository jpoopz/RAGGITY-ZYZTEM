"""
Cloud Bridge Server - FastAPI receiver for remote VPS
Receives events and vector backups from RAG System clients
"""

from fastapi import FastAPI, Request, HTTPException
import os
import json
import base64
import hashlib
import time

app = FastAPI(title="RAGGITY Cloud Bridge")

# Configuration from environment
API_KEY = os.getenv("CLOUD_KEY", "")
BACKUP_DIR = os.getenv("BACKUP_DIR", "backups")

# Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)


def verify(req_json):
    """
    Verify request signature using HMAC-style signing
    
    Args:
        req_json: Request JSON with signature and payload
        
    Raises:
        HTTPException: If signature is invalid
    """
    sig = req_json.get("signature")
    payload = req_json.get("payload", {})
    
    # Recreate signature
    body = json.dumps(payload, sort_keys=True)
    ref = hashlib.sha256((API_KEY + body).encode()).hexdigest()
    
    if sig != ref:
        print(f"[Bridge] Invalid signature: got {sig}, expected {ref}")
        raise HTTPException(status_code=403, detail="Invalid signature")


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "ts": time.time(),
        "backup_dir": BACKUP_DIR,
        "api_key_set": bool(API_KEY)
    }


@app.post("/events")
async def events(req: Request):
    """
    Receive events from clients
    
    Expected JSON:
    {
        "event": "document.indexed",
        "payload": {...},
        "ts": 1730304123.456,
        "signature": "abc123..."
    }
    """
    data = await req.json()
    
    # Verify signature
    verify(data)
    
    ev = data.get("event")
    payload = data.get("payload")
    ts = data.get("ts")
    
    print(f"[Bridge] event={ev} size={len(str(payload))} ts={ts}")
    
    # Optional: Store events to file for analytics
    event_log = os.path.join(BACKUP_DIR, "events.log")
    with open(event_log, "a", encoding="utf-8") as f:
        f.write(json.dumps({"event": ev, "payload": payload, "ts": ts}) + "\n")
    
    return {"ack": True, "event": ev}


@app.post("/backup/vector")
async def backup(req: Request):
    """
    Receive vector backup upload
    
    Expected JSON:
    {
        "file": "faiss.index",
        "data": "base64_encoded_data",
        "size": 1048576,
        "checksum": "md5_hash"
    }
    """
    data = await req.json()
    
    # Verify signature (payload is the data dict itself)
    verify({"payload": data, "signature": data.get("signature", "")})
    
    fname = data.get("file")
    b64_data = data.get("data")
    expected_size = data.get("size")
    expected_checksum = data.get("checksum")
    
    if not fname or not b64_data:
        raise HTTPException(status_code=400, detail="Missing file or data")
    
    # Decode base64
    try:
        bdata = base64.b64decode(b64_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 data: {e}")
    
    # Verify checksum if provided
    if expected_checksum:
        actual_checksum = hashlib.md5(bdata).hexdigest()
        if actual_checksum != expected_checksum:
            print(f"[Bridge] Checksum mismatch: got {actual_checksum}, expected {expected_checksum}")
            raise HTTPException(status_code=400, detail="Checksum mismatch")
    
    # Verify size if provided
    if expected_size and len(bdata) != expected_size:
        print(f"[Bridge] Size mismatch: got {len(bdata)}, expected {expected_size}")
        raise HTTPException(status_code=400, detail="Size mismatch")
    
    # Save to backup directory
    backup_path = os.path.join(BACKUP_DIR, fname)
    
    # Add timestamp to filename to keep history
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path_versioned = os.path.join(
        BACKUP_DIR,
        f"{timestamp}_{fname}"
    )
    
    try:
        with open(backup_path_versioned, "wb") as f:
            f.write(bdata)
        
        # Also save as latest
        with open(backup_path, "wb") as f:
            f.write(bdata)
        
        print(f"[Bridge] Stored backup: {fname} ({len(bdata)} bytes)")
        
        return {
            "stored": fname,
            "size": len(bdata),
            "checksum": hashlib.md5(bdata).hexdigest(),
            "versioned_file": os.path.basename(backup_path_versioned)
        }
        
    except Exception as e:
        print(f"[Bridge] Error saving backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save backup: {e}")


@app.get("/backup/vector/{filename}")
async def get_backup(filename: str):
    """
    Download a vector backup
    
    Args:
        filename: Name of backup file
        
    Returns:
        Base64-encoded file data with checksum
    """
    backup_path = os.path.join(BACKUP_DIR, filename)
    
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    
    try:
        with open(backup_path, "rb") as f:
            bdata = f.read()
        
        # Encode and checksum
        b64_data = base64.b64encode(bdata).decode()
        checksum = hashlib.md5(bdata).hexdigest()
        
        print(f"[Bridge] Sending backup: {filename} ({len(bdata)} bytes)")
        
        return {
            "file": filename,
            "data": b64_data,
            "size": len(bdata),
            "checksum": checksum
        }
        
    except Exception as e:
        print(f"[Bridge] Error reading backup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read backup: {e}")


@app.get("/backup/list")
async def list_backups():
    """List all available backups"""
    try:
        files = []
        for fname in os.listdir(BACKUP_DIR):
            fpath = os.path.join(BACKUP_DIR, fname)
            if os.path.isfile(fpath) and not fname.endswith(".log"):
                stat = os.stat(fpath)
                files.append({
                    "filename": fname,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        return {
            "backups": files,
            "count": len(files),
            "backup_dir": BACKUP_DIR
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {e}")


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("RAGGITY Cloud Bridge Server")
    print("=" * 60)
    print(f"Backup directory: {BACKUP_DIR}")
    print(f"API key set: {bool(API_KEY)}")
    print("")
    print("Endpoints:")
    print("  GET  /health - Health check")
    print("  POST /events - Receive events")
    print("  POST /backup/vector - Upload vector backup")
    print("  GET  /backup/vector/{filename} - Download backup")
    print("  GET  /backup/list - List all backups")
    print("")
    print("Starting server on 0.0.0.0:9000...")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=9000)
