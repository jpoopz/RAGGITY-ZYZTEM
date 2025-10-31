"""
RAG Engine - Pluggable vector store (FAISS or Chroma) for document ingestion and query
"""

from __future__ import annotations

import os
import glob
import threading
from typing import List, Dict, Any, Optional, Callable

from .paths import ensure_dirs, get_vector_dir, get_data_dir
from .config import CFG
from logger import get_logger
from .llm_connector import LLMConnector
from .prof import span

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
        
        # Thread safety for index writes
        self._index_lock = threading.Lock()
        
        # Batch size for embeddings
        self.batch_size = 64
        
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
        """Load texts from file or directory with multiple format support"""
        texts = []
        if os.path.isdir(path):
            files = glob.glob(os.path.join(path, "**/*"), recursive=True)
        else:
            files = [path]
        
        for f in files:
            if not os.path.isfile(f):
                continue
            
            ext = f.lower()
            
            if ext.endswith(".txt"):
                try:
                    with open(f, "r", encoding="utf-8", errors="ignore") as file:
                        texts.append(file.read())
                except Exception as e:
                    log.error(f"Error loading {f}: {e}")
            
            elif ext.endswith(".pdf"):
                texts.extend(self._load_pdf(f))
            
            elif ext.endswith(".md") or ext.endswith(".markdown"):
                texts.extend(self._load_markdown(f))
            
            elif ext.endswith(".docx"):
                texts.extend(self._load_docx(f))
        
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
    
    def _load_markdown(self, fp: str) -> List[str]:
        """Load Markdown file"""
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                return [f.read()]
        except Exception as e:
            log.error(f"Markdown load error {fp}: {e}")
            return []
    
    def _load_docx(self, fp: str) -> List[str]:
        """Load DOCX file and extract text"""
        try:
            import docx
            doc = docx.Document(fp)
            text = "\n".join([para.text for para in doc.paragraphs])
            return [text] if text.strip() else []
        except ImportError:
            log.warning(f"python-docx not installed, skipping {fp}")
            return []
        except Exception as e:
            log.error(f"DOCX load error {fp}: {e}")
            return []

    def _chunk(self, text: str, min_size: int = 800, max_size: int = 1000, overlap_pct: float = 0.12) -> List[str]:
        """
        Paragraph-aware chunking with overlapping windows.
        
        Splits by double newline for paragraphs, then packs them into
        windows of ~800-1000 chars with 10-15% overlap.
        
        Args:
            text: Input text to chunk
            min_size: Minimum chunk size in characters
            max_size: Maximum chunk size in characters
            overlap_pct: Overlap percentage (0.10 = 10%, 0.15 = 15%)
        
        Returns:
            List of text chunks
        """
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        if not paragraphs:
            return []
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_len = len(para)
            
            # If adding this paragraph would exceed max_size and we have content
            if current_size + para_len > max_size and current_chunk:
                # Save current chunk
                chunks.append("\n\n".join(current_chunk))
                
                # Calculate overlap: keep last ~12% of previous chunk
                overlap_size = int(current_size * overlap_pct)
                overlap_text = "\n\n".join(current_chunk)[-overlap_size:] if overlap_size > 0 else ""
                
                # Start new chunk with overlap
                if overlap_text:
                    current_chunk = [overlap_text, para]
                    current_size = len(overlap_text) + para_len
                else:
                    current_chunk = [para]
                    current_size = para_len
            else:
                # Add paragraph to current chunk
                current_chunk.append(para)
                current_size += para_len
                
                # If we've reached a good size, save the chunk
                if current_size >= min_size:
                    chunks.append("\n\n".join(current_chunk))
                    
                    # Calculate overlap for next chunk
                    overlap_size = int(current_size * overlap_pct)
                    overlap_text = "\n\n".join(current_chunk)[-overlap_size:] if overlap_size > 0 else ""
                    
                    if overlap_text:
                        current_chunk = [overlap_text]
                        current_size = len(overlap_text)
                    else:
                        current_chunk = []
                        current_size = 0
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks

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

    def _ingest_faiss(self, path: str, progress_callback: Optional[Callable[[int, int], None]] = None):
        """
        Ingest documents into FAISS index with batched embeddings.
        
        Args:
            path: Path to documents
            progress_callback: Optional callback(current_batch, total_batches)
        """
        import numpy as np
        import json
        
        try:
            import faiss
        except ImportError:
            log.error("faiss-cpu not installed. Run: pip install faiss-cpu")
            return
        
        with span("load_and_chunk"):
            # Load and chunk texts
            log.info(f"Ingest start: {path}")
            raw_texts = self._load_texts(path)
            log.info(f"Loaded {len(raw_texts)} raw document(s)")
            
            if not raw_texts:
                raise RuntimeError(f"No documents loaded from {path}. Check file format and permissions.")
            
            texts = []
            for t in raw_texts:
                if t.strip():  # Skip empty texts
                    texts.extend(self._chunk(t))
            
            log.info(f"Chunked into {len(texts)} segment(s)")
        
        if not texts:
            raise RuntimeError(f"No chunks produced from {path}. Documents may be empty or unreadable.")
        
        # Deduplicate chunks
        with span("deduplicate"):
            unique_texts = []
            seen = set()
            for t in texts:
                t_stripped = t.strip()
                if t_stripped and t_stripped not in seen:
                    unique_texts.append(t)
                    seen.add(t_stripped)
            
            if len(unique_texts) < len(texts):
                log.info(f"Deduplicated: {len(texts)} -> {len(unique_texts)} chunks")
            texts = unique_texts
        
        log.info(f"Generating embeddings for {len(texts)} chunks in batches of {self.batch_size}...")
        
        # Generate embeddings in batches
        all_embs = []
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(0, len(texts), self.batch_size):
            batch_num = batch_idx // self.batch_size + 1
            batch = texts[batch_idx:batch_idx + self.batch_size]
            
            with span(f"embed_batch_{batch_num}"):
                try:
                    batch_embs = self.llm.embed(batch)
                    all_embs.extend(batch_embs)
                    
                    log.info(f"Batch {batch_num}/{total_batches}: embedded {len(batch)} chunks")
                    
                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(batch_num, total_batches)
                    
                except Exception as e:
                    log.error(f"Error generating embeddings for batch {batch_num}: {e}")
                    return
        
        embs = all_embs
        
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
        index_path = os.path.join(self.store_dir, "faiss.index")
        chunks_path = os.path.join(self.store_dir, "chunks.json")
        
        faiss.write_index(self.index, index_path)
        log.info(f"FAISS index saved to {index_path}")
        
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump(self.index_map, f, ensure_ascii=False, indent=2)
        log.info(f"Chunk map saved to {chunks_path}")
        
        log.info(f"Ingest complete: {len(texts)} new chunks added. Total index size: {len(self.index_map)} chunks")
        
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
