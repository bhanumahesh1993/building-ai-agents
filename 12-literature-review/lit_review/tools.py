# lit_review/tools.py
from __future__ import annotations

import os
import re

import psycopg
from google import genai
from pgvector.psycopg import register_vector

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-004")

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _client
    if _client is None:
        _client = genai.Client()
    return _client


def _get_db_url() -> str:
    """Read the DB URL at call time, not import time."""
    return os.environ["DATABASE_URL"]


def embed_text(text: str) -> list[float]:
    """Turn one string into a 768-dim embedding."""
    resp = _get_client().models.embed_content(
        model=EMBED_MODEL, contents=text)
    return resp.embeddings[0].values


def search_corpus(
    queries: list[str], k: int = 8,
) -> list[dict]:
    """Vector search per query, merged and de-duped.

    Keeps each paper's best (smallest cosine) distance
    across all the expanded queries it matched.
    """
    best: dict[str, dict] = {}
    with psycopg.connect(_get_db_url(), autocommit=True) as conn:
        register_vector(conn)
        for q in queries:
            vec = embed_text(q)
            rows = conn.execute(
                """SELECT id, title, abstract,
                          cluster_id,
                          embedding <=> %s AS dist
                   FROM papers
                   ORDER BY dist LIMIT %s""",
                (vec, k),
            ).fetchall()
            for pid, title, abstract, cid, dist in rows:
                prior = best.get(pid)
                if prior is None or dist < prior["dist"]:
                    best[pid] = {
                        "id": pid, "title": title,
                        "abstract": abstract,
                        "cluster_id": cid, "dist": dist,
                    }
    return sorted(best.values(), key=lambda r: r["dist"])


_CITE_RE = re.compile(r"\[(\d{4}\.\d{4,5})\]")


def validate_citations(
    text: str, known_ids: set[str],
) -> dict:
    """Guardrail: every bracketed ID must be in the corpus."""
    found = set(_CITE_RE.findall(text))
    bad = found - known_ids
    return {
        "cited": sorted(found),
        "hallucinated": sorted(bad),
        "clean": len(bad) == 0,
    }


_HEDGES = (
    "may", "might", "could", "suggests", "appears",
    "warrants", "preliminary", "consistent with",
)
_OVERCLAIMS = (
    "proves", "definitively", "always", "never",
    "conclusively", "guarantees",
)


def check_hedging(text: str) -> dict:
    """Guardrail: hypotheses hedge; they never assert proof."""
    low = text.lower()
    hedges = [h for h in _HEDGES if h in low]
    overclaims = [o for o in _OVERCLAIMS if o in low]
    return {
        "hedged": len(hedges) > 0,
        "overclaim_terms": overclaims,
        "ok": len(hedges) > 0 and not overclaims,
    }
