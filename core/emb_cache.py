"""
Disk-backed embedding cache for LLM embeddings.

Caches embedding vectors to disk to avoid redundant API calls
for the same text and model combination.
"""

import os
import json
import hashlib
import threading
from typing import List, Optional

from .config import CFG

_lock = threading.Lock()

CACHE_DIR = os.path.join(CFG.vector_dir, "_emb_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _key(text: str, model: str) -> str:
    """
    Generate cache key from text and model.
    
    Args:
        text: Input text
        model: Model name
    
    Returns:
        SHA256 hex digest as cache key
    """
    return hashlib.sha256((model + "\0" + text).encode("utf-8")).hexdigest()


def get(text: str, model: str) -> Optional[List[float]]:
    """
    Retrieve cached embedding vector.
    
    Args:
        text: Input text
        model: Model name
    
    Returns:
        Cached embedding vector or None if not found
    """
    fp = os.path.join(CACHE_DIR, _key(text, model) + ".json")
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # Corrupted cache entry, ignore
            return None
    return None


def put(text: str, model: str, vec: List[float]):
    """
    Store embedding vector in cache.
    
    Args:
        text: Input text
        model: Model name
        vec: Embedding vector to cache
    """
    fp = os.path.join(CACHE_DIR, _key(text, model) + ".json")
    with _lock:
        try:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(vec, f)
        except Exception:
            # Silently fail on cache write errors
            pass


def clear():
    """Clear all cached embeddings"""
    import shutil
    with _lock:
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
            os.makedirs(CACHE_DIR, exist_ok=True)


def stats() -> dict:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache stats (count, size_mb)
    """
    try:
        files = os.listdir(CACHE_DIR)
        count = len([f for f in files if f.endswith('.json')])
        
        total_size = 0
        for f in files:
            fp = os.path.join(CACHE_DIR, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
        
        return {
            "count": count,
            "size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": CACHE_DIR
        }
    except Exception:
        return {"count": 0, "size_mb": 0, "cache_dir": CACHE_DIR}

