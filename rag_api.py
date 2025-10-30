"""
FastAPI RAG API Server
Exposes RAG system as HTTP endpoints for document ingestion and querying
"""

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import time
import threading
from typing import Optional
from pydantic import BaseModel

from core.rag_engine import RAGEngine
from core.paths import ensure_dirs, get_data_dir
from core.config import CFG
from logger import get_logger

# Import academic API routes
try:
    from modules.academic.api import router as academic_router
    ACADEMIC_AVAILABLE = True
except ImportError as e:
    ACADEMIC_AVAILABLE = False
    print(f"Academic module not available: {e}")

# Import troubleshooter
try:
    from modules.smart_troubleshooter.troubleshoot import troubleshoot
    TROUBLESHOOTER_AVAILABLE = True
except ImportError as e:
    TROUBLESHOOTER_AVAILABLE = False
    print(f"Troubleshooter not available: {e}")

# Import system monitor
try:
    from modules.system_monitor.monitor import get_system_monitor
    SYSTEM_MONITOR_AVAILABLE = True
except ImportError as e:
    SYSTEM_MONITOR_AVAILABLE = False
    print(f"System monitor not available: {e}")

# Import cloud bridge for hybrid mode
try:
    from core.cloud_bridge import bridge
    BRIDGE_AVAILABLE = True
except ImportError as e:
    BRIDGE_AVAILABLE = False
    print(f"Cloud bridge not available: {e}")

log = get_logger("rag_api")

# Global lock for index writes
_index_lock = threading.Lock()

# API authentication key (optional)
API_KEY = os.getenv("API_KEY", "")

# CLOUD_KEY for bridge/settings endpoints
CLOUD_KEY = os.getenv("CLOUD_KEY", "")

app = FastAPI(title="RAGGITY ZYZTEM API")


def verify_auth(authorization: Optional[str] = Header(None)):
    """
    Verify Bearer token authentication for sensitive endpoints.
    Only enforced if API_KEY or CLOUD_KEY is set.
    """
    # If no key is set, allow access (development mode)
    if not API_KEY and not CLOUD_KEY:
        return True
    
    # Check authorization header
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Parse Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format. Use: Bearer <token>")
    
    token = parts[1]
    
    # Verify token matches API_KEY or CLOUD_KEY
    if token != API_KEY and token != CLOUD_KEY:
        raise HTTPException(status_code=403, detail="Invalid authentication token")
    
    return True

# Get CORS origins from environment or use secure defaults
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost,http://127.0.0.1,http://localhost:8000,http://127.0.0.1:8000")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

# CORS middleware - tightened to localhost by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_headers=["*"],
    allow_methods=["*"]
)

# Initialize
ensure_dirs()
rag = RAGEngine()


class IngestPathRequest(BaseModel):
    """Request model for path ingestion"""
    path: str


class QueryRequest(BaseModel):
    """Request model for queries"""
    q: str
    k: Optional[int] = 5


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "RAGGITY ZYZTEM API"}


@app.post("/ingest-file")
async def ingest_file(background_tasks: BackgroundTasks, f: UploadFile = File(...)):
    """
    Ingest a file into the RAG system
    File is saved to data directory and processed in background
    """
    dst_dir = get_data_dir()
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, f.filename)
    
    # Save uploaded file
    with open(dst, "wb") as out:
        shutil.copyfileobj(f.file, out)
    
    # Schedule ingestion in background
    background_tasks.add_task(rag.ingest_path, dst)
    
    return {"message": "ingest scheduled", "file": f.filename}


@app.post("/ingest-path")
def ingest_path(request: IngestPathRequest):
    """
    Ingest documents from a specified path
    Path can be a file or directory
    """
    path = request.path
    
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="path does not exist")
    
    rag.ingest_path(path)
    
    return {"message": "ingested", "path": path}


@app.get("/query")
def query(q: str, k: int = 5):
    """
    Query the RAG system (with optional hybrid mode delegation)
    
    Args:
        q: Query string
        k: Number of context chunks to retrieve (default: 5)
    
    Returns:
        Dictionary with answer and contexts
    """
    if not q:
        raise HTTPException(status_code=400, detail="query parameter 'q' is required")
    
    # Hybrid mode: delegate to cloud if healthy
    if CFG.hybrid_mode and BRIDGE_AVAILABLE:
        try:
            log.info(f"Hybrid mode: checking cloud health for query delegation")
            health = bridge.health()
            
            if health.get("status") == "ok":
                log.info(f"Cloud healthy, delegating query: {q[:100]}")
                
                # Send delegation event
                bridge.send_event("delegate_query", {
                    "q": q[:200],  # Truncate for privacy
                    "k": k,
                    "timestamp": time.time()
                })
                
                return {
                    "answer": "Query delegated to cloud bridge for processing",
                    "contexts": [],
                    "delegated": True,
                    "cloud_url": os.getenv("CLOUD_URL", "")
                }
        except Exception as e:
            log.warning(f"Hybrid mode delegation failed, falling back to local: {e}")
    
    # Fall back to local RAG query
    result = rag.query(q, k=k)
    
    return result


@app.get("/troubleshoot")
def troubleshoot_endpoint(hours: int = 24):
    """
    Analyze logs and provide diagnostic report with fix recommendations
    
    Args:
        hours: Number of hours to look back in logs (default: 24)
    
    Returns:
        Dictionary with:
            - issues: List of detected issues
            - recommendations: List of automated fix suggestions
            - summary: Summary statistics
            - timestamp: When analysis was performed
    """
    if not TROUBLESHOOTER_AVAILABLE:
        log.error("Troubleshooter module not available")
        raise HTTPException(
            status_code=503,
            detail="Troubleshooter module not available"
        )
    
    try:
        log.info(f"Troubleshoot request received (hours={hours})")
        
        # Run troubleshooter
        result = troubleshoot(hours=hours)
        
        log.info(f"Troubleshoot complete: {result['summary']['total_issues']} issues found")
        
        return result
        
    except Exception as e:
        log.error(f"Error in troubleshoot endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Troubleshoot failed: {str(e)}"
        )


@app.get("/system-stats")
def system_stats():
    """
    Get current system resource statistics
    
    Returns:
        Dictionary with:
            - cpu_percent: CPU usage percentage
            - mem_percent: Memory usage percentage
            - mem_used_mb: Memory used in MB
            - mem_total_mb: Total memory in MB
            - gpu: GPU status (utilization, memory, temperature, etc.)
            - ollama_running: Boolean if Ollama is accessible
            - timestamp: Unix timestamp
    """
    if not SYSTEM_MONITOR_AVAILABLE:
        log.error("System monitor module not available")
        raise HTTPException(
            status_code=503,
            detail="System monitor module not available"
        )
    
    try:
        log.info("System stats request received")
        
        # Get system monitor
        monitor = get_system_monitor()
        
        # Get current snapshot
        snapshot = monitor.get_snapshot()
        
        log.info(f"System stats: CPU {snapshot['cpu_percent']}%, RAM {snapshot['mem_percent']}%")
        
        return snapshot
        
    except Exception as e:
        log.error(f"Error in system-stats endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"System stats failed: {str(e)}"
        )


# Include academic routes if available
if ACADEMIC_AVAILABLE:
    app.include_router(academic_router)
    log.info("Academic module routes registered")


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting RAGGITY ZYZTEM API...")
    print("📡 API available at: http://0.0.0.0:8000")
    print("📚 Endpoints:")
    print("   GET  /health - Health check")
    print("   POST /ingest-file - Upload and ingest a file")
    print("   POST /ingest-path - Ingest from filesystem path")
    print("   GET  /query?q=<question>&k=<num> - Query the RAG system")
    print("   GET  /troubleshoot?hours=<hours> - Diagnostic report with fix recommendations")
    print("   GET  /system-stats - Real-time CPU/RAM/GPU metrics")
    print(f"\n🔧 Troubleshooter: {'Available' if TROUBLESHOOTER_AVAILABLE else 'Not Available'}")
    print(f"📊 System Monitor: {'Available' if SYSTEM_MONITOR_AVAILABLE else 'Not Available'}")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
