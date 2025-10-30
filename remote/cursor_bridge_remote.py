"""
Cursor Bridge Remote - VPS endpoint for forwarding diagnostics to Cursor
"""

import os
import sys
import json
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = "/var/log/julian_bridge_remote.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Cursor Bridge Remote API", version="7.5.0")

# Load config
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "cursor_bridge.json")
AUTH_TOKEN = None

try:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            AUTH_TOKEN = config.get("vps_token", "")
except:
    pass

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class DiagnosticPayload(BaseModel):
    issue_type: str
    message: str
    severity: str
    fix_suggested: Optional[dict] = None
    module: Optional[str] = None
    metadata: Optional[dict] = None

class AutoFixResponse(BaseModel):
    status: str
    message: str
    prompt_file: Optional[str] = None
    timestamp: str

# Storage for prompts (simplified - use database in production)
PROMPTS_FILE = "/tmp/julian_cursor_prompts.json"

def verify_token(authorization: Optional[str] = Header(None)):
    """Verify authentication token"""
    if not AUTH_TOKEN:
        return True  # No token configured, allow
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.split(" ")[1]
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return True

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Cursor Bridge Remote",
        "version": "7.5.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/auto_fix", response_model=AutoFixResponse)
async def auto_fix(
    payload: DiagnosticPayload,
    authorization: Optional[str] = Header(None)
):
    """
    Accept diagnostic payload and forward to Cursor CLI if tunnel open
    
    Returns prompt file path or error message
    """
    try:
        # Verify token
        verify_token(authorization)
        
        logger.info(f"Received auto_fix request: {payload.issue_type}")
        
        # Generate Cursor prompt
        prompt = generate_cursor_prompt(payload)
        
        # Save prompt to file
        prompts_data = []
        if os.path.exists(PROMPTS_FILE):
            try:
                with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                    prompts_data = json.load(f)
            except:
                prompts_data = []
        
        prompt_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "payload": payload.dict(),
            "status": "pending",
            "source": "vps_remote"
        }
        
        prompts_data.append(prompt_entry)
        
        # Keep only last 50
        prompts_data = prompts_data[-50:]
        
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(prompts_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Prompt saved to {PROMPTS_FILE}")
        
        # Try to forward to Cursor CLI if available
        # This would require SSH tunnel or direct access
        cursor_sent = try_send_to_cursor(prompt)
        
        return AutoFixResponse(
            status="success" if cursor_sent else "pending",
            message=f"Prompt saved. {'Forwarded to Cursor.' if cursor_sent else 'Awaiting Cursor connection.'}",
            prompt_file=PROMPTS_FILE,
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in auto_fix: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def generate_cursor_prompt(payload: DiagnosticPayload) -> str:
    """Generate Cursor prompt from diagnostic payload"""
    prompt_parts = []
    
    prompt_parts.append("# 🔧 Auto-Fix Request - Julian Assistant Suite VPS")
    prompt_parts.append(f"\n**Generated:** {datetime.now().isoformat()}\n")
    prompt_parts.append("## 🐛 Issue")
    prompt_parts.append(f"\n**Type:** {payload.issue_type}")
    prompt_parts.append(f"**Severity:** {payload.severity}")
    prompt_parts.append(f"**Module:** {payload.module or 'unknown'}")
    prompt_parts.append(f"\n**Message:**\n```\n{payload.message}\n```\n")
    
    if payload.fix_suggested:
        prompt_parts.append("## 💡 Suggested Fix")
        prompt_parts.append(f"\n```json\n{json.dumps(payload.fix_suggested, indent=2)}\n```\n")
    
    if payload.metadata:
        prompt_parts.append("## 📋 Metadata")
        prompt_parts.append(f"\n```json\n{json.dumps(payload.metadata, indent=2)}\n```\n")
    
    prompt_parts.append("\n## 📝 Action Required\n")
    prompt_parts.append("Please review the issue and apply the suggested fix, or propose an alternative solution.")
    prompt_parts.append("\n---\n")
    prompt_parts.append("*Generated by Cursor Bridge Remote v7.5.0*")
    
    return "\n".join(prompt_parts)

def try_send_to_cursor(prompt: str) -> bool:
    """Try to send prompt to Cursor CLI (requires tunnel)"""
    # This would typically require:
    # 1. SSH tunnel from VPS to local Cursor
    # 2. Or Cursor API endpoint exposed
    # For now, just save to file
    
    logger.info("Cursor CLI forwarding not implemented (requires tunnel setup)")
    return False

@app.get("/prompts")
async def get_prompts(authorization: Optional[str] = Header(None)):
    """Get list of pending prompts"""
    verify_token(authorization)
    
    try:
        if os.path.exists(PROMPTS_FILE):
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
                return {"prompts": prompts}
        return {"prompts": []}
    except Exception as e:
        logger.error(f"Error reading prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Cursor Bridge Remote API on port 8001")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")




