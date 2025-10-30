"""
RAG Engine - FAISS-based document ingestion and query
"""

from __future__ import annotations

import os
import glob
from typing import List, Dict, Any

from .paths import ensure_dirs, get_vector_dir, get_data_dir
from .config import CFG
from logger import get_logger
from .llm_connector import LLMConnector

log = get_logger("rag")


class RAGEngine:
    """FAISS-based RAG engine for document ingestion and querying"""
    
    def __init__(self, store_dir: str | None = None):
        ensure_dirs()
        self.store_dir = store_dir or get_vector_dir()
        os.makedirs(self.store_dir, exist_ok=True)
        self.llm = LLMConnector()
        self.index = None
        self.index_map = []

    def _load_texts(self, path: str) -> List[str]:
        """Load texts from file or directory"""
        texts = []
        if os.path.isdir(path):
            files = glob.glob(os.path.join(path, "**/*"), recursive=True)
        else:
            files = [path]
        
        for f in files:
            if not os.path.isfile(f):
                continue
            if f.lower().endswith(".txt"):
                try:
                    with open(f, "r", encoding="utf-8", errors="ignore") as file:
                        texts.append(file.read())
                except Exception as e:
                    log.error(f"Error loading {f}: {e}")
            elif f.lower().endswith(".pdf"):
                texts.extend(self._load_pdf(f))
        
        return texts

    def _load_pdf(self, fp: str) -> List[str]:
        """Load PDF file and extract text"""
        try:
            from pypdf import PdfReader
            r = PdfReader(fp)
            return [p.extract_text() or "" for p in r.pages]
        except Exception as e:
            log.error(f"PDF load error {fp}: {e}")
            return []

    def _chunk(self, text: str, size: int = 800, overlap: int = 120) -> List[str]:
        """Chunk text into overlapping segments"""
        out, i, n = [], 0, len(text)
        while i < n:
            out.append(text[i:i+size])
            i += size - overlap
        return out

    def build_or_load_index(self):
        """Build or load FAISS index from disk"""
        import json
        
        try:
            import faiss
        except ImportError:
            log.error("faiss-cpu not installed. Run: pip install faiss-cpu")
            return
        
        idx_fp = os.path.join(self.store_dir, "faiss.index")
        map_fp = os.path.join(self.store_dir, "chunks.json")
        
        if os.path.exists(idx_fp) and os.path.exists(map_fp):
            try:
                self.index = faiss.read_index(idx_fp)
                with open(map_fp, "r", encoding="utf-8") as f:
                    self.index_map = json.load(f)
                log.info(f"Loaded index with {len(self.index_map)} chunks")
                return
            except Exception as e:
                log.error(f"Error loading index: {e}")
        
        # Index will be created on first ingest
        self.index = None
        self.index_map = []

    def ingest_path(self, path: str):
        """Ingest documents from path into FAISS index"""
        import numpy as np
        import json
        
        try:
            import faiss
        except ImportError:
            log.error("faiss-cpu not installed. Run: pip install faiss-cpu")
            return
        
        # Load and chunk texts
        texts = []
        for t in self._load_texts(path):
            if t.strip():  # Skip empty texts
                texts.extend(self._chunk(t))
        
        if not texts:
            log.warning("No texts found to ingest.")
            return
        
        log.info(f"Generating embeddings for {len(texts)} chunks...")
        
        # Generate embeddings
        try:
            embs = self.llm.embed(texts)
        except Exception as e:
            log.error(f"Error generating embeddings: {e}")
            return
        
        # Convert to numpy array
        X = np.array(embs).astype("float32")
        
        # Create or update index
        if self.index is None:
            self.index = faiss.IndexFlatL2(X.shape[1])
            log.info(f"Created new FAISS index (dim={X.shape[1]})")
        
        self.index.add(X)
        self.index_map.extend(texts)
        
        # Persist to disk
        os.makedirs(self.store_dir, exist_ok=True)
        faiss.write_index(self.index, os.path.join(self.store_dir, "faiss.index"))
        
        with open(os.path.join(self.store_dir, "chunks.json"), "w", encoding="utf-8") as f:
            json.dump(self.index_map, f, ensure_ascii=False, indent=2)
        
        log.info(f"Ingested {len(texts)} chunks. Total index size: {len(self.index_map)}")

    def query(self, question: str, k: int = 5) -> Dict[str, Any]:
        """Query the RAG system"""
        import numpy as np
        
        # Load index if not already loaded
        if self.index is None or not self.index_map:
            self.build_or_load_index()
            if self.index is None or not self.index_map:
                return {
                    "answer": "No index available. Please ingest documents first.",
                    "contexts": []
                }
        
        # Generate query embedding
        try:
            qv = self.llm.embed([question])[0]
        except Exception as e:
            log.error(f"Error generating query embedding: {e}")
            return {
                "answer": f"Error generating query embedding: {e}",
                "contexts": []
            }
        
        # Search index
        D, I = self.index.search(np.array([qv]).astype("float32"), min(k, len(self.index_map)))
        
        # Retrieve contexts
        ctx = [
            self.index_map[i] 
            for i in I[0] 
            if 0 <= i < len(self.index_map)
        ]
        
        if not ctx:
            return {
                "answer": "No relevant context found.",
                "contexts": []
            }
        
        # Build prompt
        prompt = [
            {
                "role": "system",
                "content": "You are a precise assistant. Ground your answer in the provided context."
            },
            {
                "role": "user",
                "content": f"Context:\n{chr(10).join('---' + chr(10) + c for c in ctx)}\n\nQuestion: {question}\n\nAnswer concisely with citations to chunks if useful."
            }
        ]
        
        # Get answer from LLM
        try:
            ans = self.llm.chat(prompt)
        except Exception as e:
            log.error(f"Error getting LLM response: {e}")
            ans = f"Error: {e}"
        
        return {
            "answer": ans,
            "contexts": ctx
        }


# Global RAG engine instance
rag = RAGEngine()

