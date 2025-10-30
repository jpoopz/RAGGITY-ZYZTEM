"""
Smart Troubleshooter API - FastAPI endpoints for troubleshooting
"""

import os
import sys
from fastapi import FastAPI, HTTPException

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from modules.smart_troubleshooter.troubleshooter_core import get_troubleshooter
from modules.smart_troubleshooter.prompt_generator import PromptGenerator

app = FastAPI(title="Smart Troubleshooter API", version="7.0.0")

generator = PromptGenerator()

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "Smart Troubleshooter API"}

@app.post("/scan")
async def run_scan():
    """Run diagnostic scan"""
    troubleshooter = get_troubleshooter()
    result = troubleshooter.run_manual_scan()
    return result

@app.get("/issues")
async def get_issues():
    """Get recent issues"""
    troubleshooter = get_troubleshooter()
    result = troubleshooter.run_manual_scan()
    return {"issues": result.get("issues", [])[:20]}

@app.post("/generate_prompt/{issue_id}")
async def generate_prompt(issue_id: int):
    """Generate Cursor prompt for issue"""
    troubleshooter = get_troubleshooter()
    prompt = troubleshooter.generate_cursor_prompt_for_issue(issue_id)
    if prompt:
        return {"prompt": prompt}
    else:
        raise HTTPException(status_code=404, detail="Issue not found")




