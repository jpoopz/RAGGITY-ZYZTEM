"""
RAG Engine - Pluggable vector store (FAISS or Chroma) for document ingestion and query
"""

from __future__ import annotations

import os
import glob
from typing import List, Dict, Any

from .paths import ensure_dirs, get_vector_dir, get_data_dir
from .config import CFG
from logger import get_logger
from .llm_connector import LLMConnector

# Import cloud bridge for telemetry
try:
    from .cloud_bridge import bridge
    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False

log = get_logger("rag")


class RAGEngine:
    """RAG engine with pluggable vector store (FAISS or Chroma)"""
    
    def __init__(self, store_dir: str | None = None, vector_store: str | None = None):
        ensure_dirs()
        self.store_dir = store_dir or get_vector_dir()
        self.vector_store = vector_store or CFG.vector_store
        os.makedirs(self.store_dir, exist_ok=True)
        self.llm = LLMConnector()
        
        # Vector store specific state
        if self.vector_store == "faiss":
            self.index = None
            self.index_map = []
        elif self.vector_store == "chroma":
            self.collection = None
        else:
            log.warning(f"Unknown vector store: {self.vector_store}, defaulting to FAISS")
            self.vector_store = "faiss"
            self.index = None
            self.index_map = []
        
        log.info(f"RAGEngine initialized with vector_store={self.vector_store}")

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

    # ========== FAISS Implementation ==========
    
    def build_or_load_index(self):
        """Build or load index from disk (FAISS or Chroma)"""
        if self.vector_store == "faiss":
            self._build_or_load_faiss()
        elif self.vector_store == "chroma":
            self._build_or_load_chroma()

    def _build_or_load_faiss(self):
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
                log.info(f"Loaded FAISS index with {len(self.index_map)} chunks")
                return
            except Exception as e:
                log.error(f"Error loading FAISS index: {e}")
        
        # Index will be created on first ingest
        self.index = None
        self.index_map = []

    def _build_or_load_chroma(self):
        """Build or load ChromaDB collection"""
        try:
            import chromadb
        except ImportError:
            log.error("chromadb not installed. Run: pip install chromadb")
            return
        
        try:
            client = chromadb.PersistentClient(path=CFG.chroma_dir)
            self.collection = client.get_or_create_collection(
                name="rag_documents",
                metadata={"description": "RAG system documents"}
            )
            count = self.collection.count()
            log.info(f"Loaded ChromaDB collection with {count} documents")
        except Exception as e:
            log.error(f"Error loading ChromaDB: {e}")
            self.collection = None

    def ingest_path(self, path: str):
        """Ingest documents from path into vector store"""
        if self.vector_store == "faiss":
            self._ingest_faiss(path)
        elif self.vector_store == "chroma":
            self._ingest_chroma(path)

    def _ingest_faiss(self, path: str):
        """Ingest documents into FAISS index"""
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
        
        log.info(f"Ingested {len(texts)} chunks into FAISS. Total: {len(self.index_map)}")
        
        # Send telemetry event
        if BRIDGE_AVAILABLE:
            try:
                bridge.send_event("ingest_complete", {
                    "chunks": len(texts),
                    "total_chunks": len(self.index_map),
                    "vector_store": "faiss",
                    "path": os.path.basename(path)
                })
            except Exception as e:
                log.warning(f"Failed to send ingest event: {e}")
        
        # Optional: Backup to cloud
        if BRIDGE_AVAILABLE and os.getenv("AUTO_BACKUP") == "true":
            try:
                index_path = os.path.join(self.store_dir, "faiss.index")
                bridge.push_vector_backup(index_path)
                log.info("Vector backup pushed to cloud")
            except Exception as e:
                log.warning(f"Failed to push vector backup: {e}")

    def _ingest_chroma(self, path: str):
        """Ingest documents into ChromaDB"""
        import hashlib
        
        if self.collection is None:
            self._build_or_load_chroma()
            if self.collection is None:
                log.error("ChromaDB collection not available")
                return
        
        # Load and chunk texts
        texts = []
        for t in self._load_texts(path):
            if t.strip():
                texts.extend(self._chunk(t))
        
        if not texts:
            log.warning("No texts found to ingest.")
            return
        
        log.info(f"Ingesting {len(texts)} chunks into ChromaDB...")
        
        # Generate IDs for chunks
        ids = [hashlib.md5(f"{path}_{i}".encode()).hexdigest() for i in range(len(texts))]
        
        # ChromaDB will generate embeddings automatically if configured
        # Or we can provide our own embeddings
        try:
            embs = self.llm.embed(texts)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embs
            )
            
            log.info(f"Ingested {len(texts)} chunks into ChromaDB. Total: {self.collection.count()}")
            
            # Send telemetry event
            if BRIDGE_AVAILABLE:
                try:
                    bridge.send_event("ingest_complete", {
                        "chunks": len(texts),
                        "total_chunks": self.collection.count(),
                        "vector_store": "chroma",
                        "path": os.path.basename(path)
                    })
                except Exception as e:
                    log.warning(f"Failed to send ingest event: {e}")
                    
        except Exception as e:
            log.error(f"Error ingesting into ChromaDB: {e}")

    def query(self, question: str, k: int = 5) -> Dict[str, Any]:
        """Query the RAG system"""
        if self.vector_store == "faiss":
            return self._query_faiss(question, k)
        elif self.vector_store == "chroma":
            return self._query_chroma(question, k)

    def _query_faiss(self, question: str, k: int) -> Dict[str, Any]:
        """Query using FAISS index"""
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
        
        # Get answer from LLM
        ans = self._generate_answer(question, ctx)
        
        # Send telemetry event
        if BRIDGE_AVAILABLE:
            try:
                bridge.send_event("query", {
                    "q": question[:200],  # Truncate long queries
                    "answer": ans[:120],  # Truncate long answers
                    "contexts": len(ctx),
                    "vector_store": "faiss"
                })
            except Exception as e:
                log.warning(f"Failed to send query event: {e}")
        
        return {
            "answer": ans,
            "contexts": ctx,
            "vector_store": "faiss"
        }

    def _query_chroma(self, question: str, k: int) -> Dict[str, Any]:
        """Query using ChromaDB"""
        if self.collection is None:
            self._build_or_load_chroma()
            if self.collection is None:
                return {
                    "answer": "No ChromaDB collection available. Please ingest documents first.",
                    "contexts": []
                }
        
        try:
            # Query collection
            results = self.collection.query(
                query_texts=[question],
                n_results=k
            )
            
            # Extract contexts
            ctx = results.get("documents", [[]])[0] if results.get("documents") else []
            
            if not ctx:
                return {
                    "answer": "No relevant context found.",
                    "contexts": []
                }
            
            # Get answer from LLM
            ans = self._generate_answer(question, ctx)
            
            # Send telemetry event
            if BRIDGE_AVAILABLE:
                try:
                    bridge.send_event("query", {
                        "q": question[:200],
                        "answer": ans[:120],
                        "contexts": len(ctx),
                        "vector_store": "chroma"
                    })
                except Exception as e:
                    log.warning(f"Failed to send query event: {e}")
            
            return {
                "answer": ans,
                "contexts": ctx,
                "vector_store": "chroma"
            }
        except Exception as e:
            log.error(f"Error querying ChromaDB: {e}")
            return {
                "answer": f"Error querying ChromaDB: {e}",
                "contexts": []
            }

    def _generate_answer(self, question: str, contexts: List[str]) -> str:
        """Generate answer from contexts using LLM"""
        # Build prompt
        prompt = [
            {
                "role": "system",
                "content": "You are a precise assistant. Ground your answer in the provided context."
            },
            {
                "role": "user",
                "content": f"Context:\n{chr(10).join('---' + chr(10) + c for c in contexts)}\n\nQuestion: {question}\n\nAnswer concisely with citations to chunks if useful."
            }
        ]
        
        # Get answer from LLM
        try:
            ans = self.llm.chat(prompt)
        except Exception as e:
            log.error(f"Error getting LLM response: {e}")
            ans = f"Error: {e}"
        
        return ans


# Global RAG engine instance
rag = RAGEngine()
