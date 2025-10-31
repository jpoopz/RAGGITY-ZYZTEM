"""
Hybrid retrieval combining dense (semantic) and sparse (BM25) search.

Uses Reciprocal Rank Fusion (RRF) to merge rankings from:
- Dense: SentenceTransformers embeddings + cosine similarity
- Sparse: BM25 term-based ranking

RRF formula: score(d) = Σ 1/(k + rank_i(d))
where k=60 typically, rank_i is position in ranking i (1-indexed)
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

from logger import get_logger

log = get_logger("hybrid_retrieval")


@dataclass
class RankedResult:
    """Single ranked result with scores"""
    text: str
    score: float
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None


class HybridRetriever:
    """
    Hybrid retrieval using dense embeddings + BM25.
    
    Combines results via Reciprocal Rank Fusion (RRF).
    """
    
    def __init__(self, dense_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 bm25_impl: str = "rank_bm25",
                 rrf_k: int = 60):
        """
        Initialize hybrid retriever.
        
        Args:
            dense_model: SentenceTransformers model name
            bm25_impl: BM25 implementation ("rank_bm25" or "bm25s")
            rrf_k: RRF parameter (typically 60)
        """
        self.rrf_k = rrf_k
        self.bm25_impl = bm25_impl
        
        # Initialize dense model
        try:
            from sentence_transformers import SentenceTransformer
            self.dense_encoder = SentenceTransformer(dense_model)
            log.info(f"Loaded dense model: {dense_model}")
        except ImportError:
            log.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            self.dense_encoder = None
        except Exception as e:
            log.error(f"Failed to load dense model: {e}")
            self.dense_encoder = None
        
        # BM25 index (built on demand)
        self.bm25_index = None
        self.corpus = []
        self.dense_vectors = None
    
    def index(self, documents: List[str]):
        """
        Build dense and sparse indices.
        
        Args:
            documents: List of text documents to index
        """
        if not documents:
            log.warning("No documents to index")
            return
        
        self.corpus = documents
        log.info(f"Indexing {len(documents)} documents...")
        
        # Build dense index
        if self.dense_encoder:
            try:
                log.info("Building dense vectors...")
                self.dense_vectors = self.dense_encoder.encode(
                    documents,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
                log.info(f"Dense vectors: {self.dense_vectors.shape}")
            except Exception as e:
                log.error(f"Dense encoding failed: {e}")
                self.dense_vectors = None
        
        # Build BM25 index
        try:
            log.info("Building BM25 index...")
            
            if self.bm25_impl == "bm25s":
                try:
                    import bm25s
                    # Tokenize corpus
                    corpus_tokens = bm25s.tokenize(documents, stopwords="en")
                    self.bm25_index = bm25s.BM25()
                    self.bm25_index.index(corpus_tokens)
                    log.info("BM25 index built (bm25s)")
                except ImportError:
                    log.warning("bm25s not installed, falling back to rank_bm25")
                    self._build_rank_bm25(documents)
            else:
                self._build_rank_bm25(documents)
        
        except Exception as e:
            log.error(f"BM25 indexing failed: {e}")
            self.bm25_index = None
    
    def _build_rank_bm25(self, documents: List[str]):
        """Build BM25 index using rank_bm25"""
        try:
            from rank_bm25 import BM25Okapi
            
            # Tokenize
            tokenized_corpus = [doc.lower().split() for doc in documents]
            self.bm25_index = BM25Okapi(tokenized_corpus)
            log.info("BM25 index built (rank_bm25)")
        except ImportError:
            log.error("rank_bm25 not installed. Run: pip install rank-bm25")
            self.bm25_index = None
    
    def query_hybrid(self, query: str, top_k: int = 12) -> List[RankedResult]:
        """
        Query using hybrid retrieval with RRF fusion.
        
        Args:
            query: Query text
            top_k: Number of results to return
        
        Returns:
            List of RankedResult objects sorted by RRF score
        """
        if not self.corpus:
            log.warning("No corpus indexed")
            return []
        
        # Get dense ranking
        dense_scores = self._query_dense(query) if self.dense_vectors is not None else None
        
        # Get sparse ranking
        sparse_scores = self._query_sparse(query) if self.bm25_index is not None else None
        
        # Fuse rankings
        if dense_scores is None and sparse_scores is None:
            log.error("No retrieval methods available")
            return []
        
        fused = self._reciprocal_rank_fusion(dense_scores, sparse_scores)
        
        # Build results
        results = []
        for idx, rrf_score in fused[:top_k]:
            result = RankedResult(
                text=self.corpus[idx],
                score=rrf_score,
                dense_rank=dense_scores[idx][1] + 1 if dense_scores and idx < len(dense_scores) else None,
                sparse_rank=sparse_scores[idx][1] + 1 if sparse_scores and idx < len(sparse_scores) else None,
                dense_score=dense_scores[idx][0] if dense_scores and idx < len(dense_scores) else None,
                sparse_score=sparse_scores[idx][0] if sparse_scores and idx < len(sparse_scores) else None
            )
            results.append(result)
        
        log.info(f"Hybrid query returned {len(results)} results (RRF k={self.rrf_k})")
        return results
    
    def _query_dense(self, query: str) -> List[Tuple[int, int, float]]:
        """
        Query using dense embeddings.
        
        Returns:
            List of (doc_idx, rank, score) tuples sorted by score desc
        """
        if self.dense_encoder is None or self.dense_vectors is None:
            return []
        
        try:
            # Encode query
            query_vec = self.dense_encoder.encode([query], convert_to_numpy=True)[0]
            
            # Cosine similarity
            similarities = np.dot(self.dense_vectors, query_vec)
            
            # Rank by similarity (descending)
            ranked_indices = np.argsort(similarities)[::-1]
            
            return [(int(idx), rank, float(similarities[idx])) 
                    for rank, idx in enumerate(ranked_indices)]
        
        except Exception as e:
            log.error(f"Dense query failed: {e}")
            return []
    
    def _query_sparse(self, query: str) -> List[Tuple[int, int, float]]:
        """
        Query using BM25.
        
        Returns:
            List of (doc_idx, rank, score) tuples sorted by score desc
        """
        if self.bm25_index is None:
            return []
        
        try:
            if self.bm25_impl == "bm25s":
                # bm25s implementation
                import bm25s
                query_tokens = bm25s.tokenize([query], stopwords="en")
                results, scores = self.bm25_index.retrieve(query_tokens, k=len(self.corpus))
                
                # Flatten results
                ranked = [(int(results[0][i]), i, float(scores[0][i])) 
                         for i in range(len(results[0]))]
            else:
                # rank_bm25 implementation
                query_tokens = query.lower().split()
                scores = self.bm25_index.get_scores(query_tokens)
                
                # Rank by score
                ranked_indices = np.argsort(scores)[::-1]
                ranked = [(int(idx), rank, float(scores[idx])) 
                         for rank, idx in enumerate(ranked_indices)]
            
            return ranked
        
        except Exception as e:
            log.error(f"Sparse query failed: {e}")
            return []
    
    def _reciprocal_rank_fusion(self, 
                               dense_results: Optional[List[Tuple[int, int, float]]],
                               sparse_results: Optional[List[Tuple[int, int, float]]]) -> List[Tuple[int, float]]:
        """
        Fuse rankings using Reciprocal Rank Fusion.
        
        RRF score for document d: Σ 1/(k + rank_i(d))
        where k is a constant (typically 60), rank_i is 1-indexed rank in system i
        
        Args:
            dense_results: (doc_idx, rank, score) from dense retrieval
            sparse_results: (doc_idx, rank, score) from sparse retrieval
        
        Returns:
            List of (doc_idx, rrf_score) sorted by rrf_score desc
        """
        rrf_scores = {}
        
        # Add dense scores
        if dense_results:
            for doc_idx, rank, score in dense_results:
                # rank is 0-indexed, convert to 1-indexed for RRF
                rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0) + 1.0 / (self.rrf_k + rank + 1)
        
        # Add sparse scores
        if sparse_results:
            for doc_idx, rank, score in sparse_results:
                rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0) + 1.0 / (self.rrf_k + rank + 1)
        
        # Sort by RRF score descending
        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        return ranked


