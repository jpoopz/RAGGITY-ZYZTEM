"""
VPS Server - FastAPI server for Hostinger VPS
Lightweight automation endpoints
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

try:
    from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Depends, Header
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("ERROR: fastapi and uvicorn required for VPS server")
    print("Install with: pip install fastapi uvicorn")
    sys.exit(1)

app = FastAPI(title="Julian Assistant VPS Automation")

# Simple auth (can be enhanced)
VPS_AUTH_TOKEN = os.environ.get("VPS_AUTH_TOKEN", "")

def verify_token(authorization: str = Header(None)):
    """Verify authorization token"""
    if not VPS_AUTH_TOKEN:
        return True  # No auth required if not set
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "").strip()
    if token != VPS_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return True

class WebRetrieveRequest(BaseModel):
    query: str = ""
    url: str = ""
    source: str = "web_retriever"

@app.get("/ping")
async def ping():
    """Health check"""
    return {
        "status": "ok",
        "service": "VPS Automation Server",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/web_retrieve")
async def web_retrieve(request: WebRetrieveRequest, authorized: bool = Depends(verify_token)):
    """Web retrieval endpoint"""
    try:
        query = request.query
        url = request.url
        
        # Simple web retrieval
        import requests
        from bs4 import BeautifulSoup
        
        if url:
            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)[:5000]
            
            return {
                "status": "success",
                "summary": text[:500] + "..." if len(text) > 500 else text,
                "url": url,
                "source": "vps"
            }
        
        if query:
            # Use DuckDuckGo if available
            try:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=2))
                
                combined = "\n\n".join([r.get("body", "") for r in results])
                return {
                    "status": "success",
                    "summary": combined[:500],
                    "query": query,
                    "sources": [r.get("href", "") for r in results],
                    "source": "vps_ddg"
                }
            except ImportError:
                return {
                    "status": "partial",
                    "message": "DuckDuckGo not available on VPS",
                    "query": query
                }
        
        return {"status": "error", "message": "query or url required"}
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.post("/sync_backup")
async def sync_backup(
    backup: UploadFile = File(...),
    authorized: bool = Depends(verify_token)
):
    """Receive vault backup"""
    try:
        backup_dir = Path("/home/user/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"vault_backup_{timestamp}.tar.gz"
        
        with open(backup_path, 'wb') as f:
            content = await backup.read()
            f.write(content)
        
        return {
            "status": "success",
            "backup_path": str(backup_path),
            "size_mb": len(content) / (1024 * 1024)
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

if __name__ == "__main__":
    port = int(os.environ.get("VPS_PORT", "8000"))
    host = os.environ.get("VPS_HOST", "0.0.0.0")
    
    print(f"Starting VPS Automation Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)




