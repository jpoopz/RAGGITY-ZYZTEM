"""
FastAPI RAG API Server
Exposes RAG system as HTTP endpoints for document ingestion and querying
"""

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import time
import threading
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi.responses import StreamingResponse, JSONResponse
import json
import socket
import shutil as _shutil
import platform
from typing import Any, Dict, List
try:
    import psutil as _psutil  # optional
except Exception:
    _psutil = None
import requests as _requests

from core.io_safety import safe_reconfigure_streams
safe_reconfigure_streams()
from core.rag_engine import RAGEngine
from core.paths import ensure_dirs, get_data_dir
from core.config import CFG
from logger import get_logger
from core.settings_env import settings  # new

# Guardrails for prod profile
if settings.APP_ENV == "prod" and settings.DEBUG:
    raise RuntimeError("Refusing to start: DEBUG=true in prod profile")

# Academic API routes integrated directly below (simplified version)
ACADEMIC_AVAILABLE = True

# Import troubleshooter
try:
    from modules.smart_troubleshooter.troubleshoot import troubleshoot
    TROUBLESHOOTER_AVAILABLE = True
except ImportError as e:
    TROUBLESHOOTER_AVAILABLE = False
    log.warning(f"Troubleshooter not available: {e}")

# Import system monitor
try:
    from modules.system_monitor.monitor import get_system_monitor
    SYSTEM_MONITOR_AVAILABLE = True
except ImportError as e:
    SYSTEM_MONITOR_AVAILABLE = False
    log.warning(f"System monitor not available: {e}")

# Import cloud bridge for hybrid mode
try:
    from core.cloud_bridge import bridge
    BRIDGE_AVAILABLE = True
except ImportError as e:
    BRIDGE_AVAILABLE = False
    log.warning(f"Cloud bridge not available: {e}")

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


# Request logging middleware
@app.middleware("http")
async def _log_requests(request: Request, call_next):
    _t0 = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - _t0) * 1000.0
    try:
        log.info(f"{request.method} {request.url.path} -> {response.status_code} ({elapsed_ms:.1f}ms)")
    except Exception:
        pass
    return response


def _probe_clo(host: str = "127.0.0.1", port: int = 51235, timeout: float = 0.6):
    """TCP probe expecting {"pong":"clo"}. Returns (ok, handshake_tag)."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            payload = json.dumps({"ping": "clo"}).encode("utf-8")
            s.sendall(payload + b"\n")
            data = s.recv(256)
            try:
                resp = json.loads(data.decode("utf-8", errors="ignore"))
            except Exception:
                return False, "wrong_service"
            if resp.get("pong") == "clo":
                return True, "ok"
            return False, "wrong_service"
    except socket.timeout:
        return False, "timeout"


def _read_clo_endpoint():
    """Read CLO endpoint from config or environment."""
    host, port = "127.0.0.1", 51235
    try:
        with open(os.path.join("config", "academic_rag_config.json"), "r", encoding="utf-8") as f:
            j = json.load(f)
            host = j.get("clo_host", j.get("CLO_HOST", host)) or host
            try:
                port = int(j.get("clo_port", j.get("CLO_PORT", port)) or port)
            except Exception:
                pass
    except Exception:
        pass
    host = os.getenv("CLO_HOST", host)
    try:
        port = int(os.getenv("CLO_PORT", str(port)))
    except Exception:
        pass
    return host, port


def _probe_clo_tcp(host: str, port: int):
    """Server-side TCP probe with optional pong handshake."""
    try:
        with socket.create_connection((host, int(port)), timeout=0.8) as s:
            try:
                s.sendall((json.dumps({"ping": "clo"}) + "\n").encode("utf-8"))
                s.settimeout(0.8)
                data = s.recv(4096)
                if b"pong" in data:
                    return True, "pong"
            except Exception:
                pass
            return True, "tcp_ok"
    except Exception as e:
        return False, type(e).__name__


@app.get("/health/clo")
def health_clo():
    h, p = _read_clo_endpoint()
    ok, detail = _probe_clo_tcp(h, p)
    return JSONResponse({"ok": bool(ok), "handshake": detail, "host": h, "port": p})
    except Exception:
        return False, "timeout"


def _probe_ollama(model: str | None = None):
    base = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    try:
        r = _requests.get(f"{base}/api/tags", timeout=0.8)
        if r.status_code != 200:
            return {"ok": False, "model_ok": False, "model": model or ""}
        tags = r.json().get("models", [])
        have = {m.get("name", "").split(":")[0] for m in tags}
        if model:
            return {"ok": True, "model_ok": model in have, "model": model}
        return {"ok": True, "model_ok": True if have else False, "model": next(iter(have)) if have else ""}
    except Exception:
        return {"ok": False, "model_ok": False, "model": model or ""}


@app.get("/health/full")
def health_full():
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", "5000"))
    clo_host = os.getenv("CLO_HOST", "127.0.0.1")
    clo_port = int(os.getenv("CLO_PORT", "51235"))
    vector_store = getattr(getattr(rag, "config", CFG), "vector_store", getattr(CFG, "vector_store", "faiss"))
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")

    clo_ok, handshake = _probe_clo(clo_host, clo_port)
    ollama = _probe_ollama(ollama_model)

    # System
    disk_free_gb = None
    ram_free_gb = None
    try:
        total, used, free = _shutil.disk_usage(os.getcwd())
        disk_free_gb = round(free / (1024**3), 2)
    except Exception:
        pass
    try:
        if _psutil:
            ram_free_gb = round((_psutil.virtual_memory().available) / (1024**3), 2)
    except Exception:
        pass

    return {
        "api": {"ok": True, "host": api_host, "port": api_port},
        "clo": {"ok": bool(clo_ok), "host": clo_host, "port": clo_port, "handshake": handshake},
        "vector_store": vector_store,
        "ollama": ollama,
        "sys": {
            "disk_free_gb": disk_free_gb if disk_free_gb is not None else 0.0,
            "ram_free_gb": ram_free_gb if ram_free_gb is not None else 0.0,
            "py": platform.python_version(),
        },
    }


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

@app.post("/query")
def query_post(body: QueryRequest):
    return query(q=body.q, k=body.k or 5)


@app.get("/query_stream")
def query_stream(
    q: str = Query(...),
    top_k: int = 5,
    temperature: float = 0.3,
):
    """Server-Sent Events stream of tokens with heartbeats and final sources."""
    if not q:
        raise HTTPException(status_code=400, detail="query parameter 'q' is required")

    try:
        result = rag.query(q, k=top_k)
        answer = result.get("answer", "")
        sources = result.get("contexts", [])
    except Exception as e:
        log.error(f"/query_stream failed: {e}")
        raise HTTPException(status_code=500, detail="query failed")

    def gen():
        last_hb = time.time()
        try:
            for ch in answer:
                now = time.time()
                if now - last_hb > 10:
                    # heartbeat to keep proxies alive
                    yield ": keep-alive\n\n"
                    last_hb = now
                yield f"data: {json.dumps({'delta': ch})}\n\n"
            yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"
        except Exception:
            yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


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


# Academic routes - simplified implementation
try:
    from modules.academic.providers import search_openalex, search_arxiv, fetch_crossref_by_doi, unpaywall_best, unify
    from citations.harvard import crossref_to_csl, render_bibliography, inline_cite
    
    @app.get("/academic/search")
    def academic_search(q: str, openalex: bool = True, arxiv: bool = True):
        items = []
        if openalex:
            items += search_openalex(q)
        if arxiv:
            items += search_arxiv(q)
        return {"results": unify(items)}
    
    @app.post("/academic/cite")
    def academic_cite(body: Dict[str, Any]):
        dois: List[str] = body.get("dois", [])
        csl_items = []
        inlines = []
        for doi in dois:
            try:
                meta = fetch_crossref_by_doi(doi)
                csl = crossref_to_csl(meta)
                csl_items.append(csl)
                authors = [a.get("family","") for a in csl.get("author", []) if a.get("family")]
                year = None
                try:
                    year = csl.get("issued", {}).get("date-parts", [[None]])[0][0]
                    year = int(year) if year else None
                except Exception:
                    pass
                inlines.append(inline_cite(authors, year))
            except Exception as e:
                inlines.append("(n.d.)")
        bib = render_bibliography(csl_items) if csl_items else []
        return {"inline": "; ".join(inlines), "bibliography": bib}
    
    @app.get("/academic/unpaywall")
    def academic_unpaywall(doi: str):
        return unpaywall_best(doi) or {}
    
    log.info("Academic routes registered (simplified)")
    
except ImportError as e:
    log.warning(f"Academic routes not available: {e}")


if __name__ == "__main__":
    import uvicorn
    log.info("🚀 Starting RAGGITY ZYZTEM API...")
    log.info("📡 API available at: http://0.0.0.0:8000")
    log.info("📚 Endpoints:")
    log.info("   GET  /health - Health check")
    log.info("   POST /ingest-file - Upload and ingest a file")
    log.info("   POST /ingest-path - Ingest from filesystem path")
    log.info("   GET  /query?q=<question>&k=<num> - Query the RAG system")
    log.info("   GET  /troubleshoot?hours=<hours> - Diagnostic report with fix recommendations")
    log.info("   GET  /system-stats - Real-time CPU/RAM/GPU metrics")
    log.info(f"🔧 Troubleshooter: {'Available' if TROUBLESHOOTER_AVAILABLE else 'Not Available'}")
    log.info(f"📊 System Monitor: {'Available' if SYSTEM_MONITOR_AVAILABLE else 'Not Available'}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
