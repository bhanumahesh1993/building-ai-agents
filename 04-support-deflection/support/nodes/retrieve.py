# support/nodes/retrieve.py
from __future__ import annotations

import os

import psycopg
from openai import OpenAI

from ..state import TicketState

EMBED_MODEL = "text-embedding-3-small"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _get_db_url() -> str:
    """Read the DB URL lazily so import doesn't require
    it to be set (tests, offline use)."""
    return os.environ["DATABASE_URL"]


RRF_SQL = """
WITH vec AS (
  SELECT id, ROW_NUMBER() OVER (
    ORDER BY embedding <=> %(qvec)s) AS rank
  FROM kb_chunks
  ORDER BY embedding <=> %(qvec)s
  LIMIT 20
),
kw AS (
  SELECT id, ROW_NUMBER() OVER (
    ORDER BY ts_rank(tsv, q) DESC) AS rank
  FROM kb_chunks, plainto_tsquery(%(text)s) q
  WHERE tsv @@ q
  LIMIT 20
),
fused AS (
  SELECT COALESCE(vec.id, kw.id) AS id,
    1.0 / (60 + COALESCE(vec.rank, 999)) +
    1.0 / (60 + COALESCE(kw.rank, 999)) AS score
  FROM vec FULL OUTER JOIN kw ON vec.id = kw.id
)
SELECT c.doc, c.section, c.url, c.body
FROM fused f
JOIN kb_chunks c ON c.id = f.id
ORDER BY f.score DESC
LIMIT %(k)s;
"""


def embed(text: str) -> list[float]:
    """Embed with the same model ingest.py used."""
    resp = _get_client().embeddings.create(
        model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


def retrieve_node(state: TicketState) -> dict:
    """Hybrid (vector + keyword) search over the KB."""
    qvec = embed(state["message"])
    with psycopg.connect(_get_db_url()) as conn:
        rows = conn.execute(RRF_SQL, {
            "qvec": qvec,
            "text": state["message"],
            "k": 5,
        }).fetchall()
    hits = [
        {"doc": r[0], "section": r[1],
         "url": r[2], "body": r[3]}
        for r in rows
    ]
    return {
        "kb_hits": hits,
        "events": [
            {"node": "retrieve", "hits": len(hits)}],
    }
