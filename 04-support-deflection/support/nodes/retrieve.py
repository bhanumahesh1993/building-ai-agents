# support/nodes/retrieve.py
from __future__ import annotations

import os

import psycopg
from openai import OpenAI

from ..state import TicketState

DB_URL = os.environ["DATABASE_URL"]
EMBED_MODEL = "text-embedding-3-small"

_client = OpenAI()

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
    resp = _client.embeddings.create(
        model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


def retrieve_node(state: TicketState) -> dict:
    """Hybrid (vector + keyword) search over the KB."""
    qvec = embed(state["message"])
    with psycopg.connect(DB_URL) as conn:
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
