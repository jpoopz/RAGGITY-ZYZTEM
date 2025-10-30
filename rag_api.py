"""
FastAPI RAG API Server
Exposes RAG system as HTTP endpoints for document ingestion and querying
"""

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from typing import Optional
from pydantic import BaseModel

from core.rag_engine import RAGEngine
from core.paths import ensure_dirs, get_data_dir
from core.config import CFG

app = FastAPI(title="RAGGITY ZYZTEM API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    Query the RAG system
    
    Args:
        q: Query string
        k: Number of context chunks to retrieve (default: 5)
    
    Returns:
        Dictionary with answer and contexts
    """
    if not q:
        raise HTTPException(status_code=400, detail="query parameter 'q' is required")
    
    result = rag.query(q, k=k)
    
    return result


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting RAGGITY ZYZTEM API...")
    print("📡 API available at: http://0.0.0.0:8000")
    print("📚 Endpoints:")
    print("   GET  /health - Health check")
    print("   POST /ingest-file - Upload and ingest a file")
    print("   POST /ingest-path - Ingest from filesystem path")
    print("   GET  /query?q=<question>&k=<num> - Query the RAG system")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
