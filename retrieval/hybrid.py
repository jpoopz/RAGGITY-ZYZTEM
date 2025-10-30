# retrieval/hybrid.py
from __future__ import annotations

from typing import List, Dict, Any, Tuple
import numpy as np


class BM25Wrapper:
    def __init__(self, docs: List[str]):
        from rank_bm25 import BM25Okapi
        self.tokens = [d.split() for d in docs]
        self.bm25 = BM25Okapi(self.tokens)

    def search(self, q: str, k: int) -> List[Tuple[int, float]]:
        toks = q.split()
        scores = self.bm25.get_scores(toks)
        order = np.argsort(scores)[::-1][:k]
        return [(int(i), float(scores[i])) for i in order]


class DenseWrapper:
    def __init__(self, docs: List[str], encode_fn):
        self.docs = docs
        self.encode = encode_fn
        self.emb = np.array(self.encode(docs)).astype("float32")
        self.norm = self.emb / (np.linalg.norm(self.emb, axis=1, keepdims=True) + 1e-8)

    def search(self, q: str, k: int) -> List[Tuple[int, float]]:
        qv = np.array(self.encode([q])[0]).astype("float32")
        qv = qv / (np.linalg.norm(qv) + 1e-8)
        sims = self.norm @ qv
        order = np.argsort(sims)[::-1][:k]
        return [(int(i), float(sims[i])) for i in order]


def rrf_fuse(bm: List[Tuple[int,float]], de: List[Tuple[int,float]], k: int = 60, top_k: int = 12):
    # Reciprocal Rank Fusion: sum_i 1/(k + rank_i)
    from collections import defaultdict
    rankmap = defaultdict(float)
    for rank, (i, _) in enumerate(bm):
        rankmap[i] += 1.0 / (k + rank + 1)
    for rank, (i, _) in enumerate(de):
        rankmap[i] += 1.0 / (k + rank + 1)
    fused = sorted(rankmap.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return fused  # [(doc_index, fused_score)]

