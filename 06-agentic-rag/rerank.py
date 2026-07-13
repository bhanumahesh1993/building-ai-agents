# rerank.py — cross-encoder reranks the shortlist
from __future__ import annotations

import os

import cohere

RERANK_MODEL = os.getenv(
    "RERANK_MODEL", "rerank-v3.5")

_co = cohere.Client(os.environ["COHERE_API_KEY"])


def rerank(
    query: str, candidates: list[dict], k: int = 6,
) -> list[dict]:
    """Re-score a shortlist jointly; keep the top k."""
    if not candidates:
        return []
    docs = [c["body"] for c in candidates]
    resp = _co.rerank(
        model=RERANK_MODEL, query=query,
        documents=docs,
        top_n=min(k, len(docs)))
    return [
        {**candidates[r.index],
         "rerank_score": r.relevance_score}
        for r in resp.results
    ]
