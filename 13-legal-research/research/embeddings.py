# research/embeddings.py
from __future__ import annotations

from openai import OpenAI

EMBED_MODEL = "text-embedding-3-small"  # 1536 dims

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def embed(text: str) -> list[float]:
    """Turn one string into a 1536-dim vector for the
    pgvector similarity search in corpus.py."""
    resp = _get_client().embeddings.create(
        model=EMBED_MODEL, input=text)
    return resp.data[0].embedding
