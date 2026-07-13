# index.py — hybrid retrieval over pgvector
from __future__ import annotations

from typing import Protocol

from .ingest import embed

RRF_K = 60  # standard smoothing constant


class VectorStore(Protocol):
    """What every retrieval backend must implement."""

    def hybrid_search(
        self, query: str, k: int, acl: list[str],
    ) -> list[dict]:
        ...


def rrf_fuse(
    vector_ranked: list[str],
    keyword_ranked: list[str],
    k: int = 20,
    rrf_k: int = RRF_K,
) -> list[tuple[str, float]]:
    """Pure reciprocal-rank fusion, mirroring the SQL
    CTE above so the scoring math is unit-testable
    without a live Postgres connection.

    ``vector_ranked`` / ``keyword_ranked`` are chunk ids
    in descending relevance order from each retriever.
    Returns (id, score) pairs sorted by fused score.
    """
    vec_rank = {
        cid: i + 1 for i, cid in enumerate(vector_ranked)}
    kw_rank = {
        cid: i + 1 for i, cid in enumerate(keyword_ranked)}
    ids = set(vec_rank) | set(kw_rank)
    scored = [
        (cid,
         1.0 / (rrf_k + vec_rank.get(cid, 999))
         + 1.0 / (rrf_k + kw_rank.get(cid, 999)))
        for cid in ids
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:k]


class PgVectorStore:
    """Default backend: pgvector + Postgres full text."""

    def __init__(self, conn):
        self.conn = conn

    def hybrid_search(
        self, query: str, k: int = 20,
        acl: list[str] | None = None,
    ) -> list[dict]:
        """Vector + BM25 candidates, fused by RRF."""
        qvec = embed(query)
        acl = acl or ["public"]
        rows = self.conn.execute(
            """
            WITH vec AS (
              SELECT id, ROW_NUMBER() OVER (
                ORDER BY embedding <=> %(qv)s
              ) AS rnk
              FROM chunks
              WHERE acl_tags && %(acl)s
              ORDER BY embedding <=> %(qv)s
              LIMIT 20
            ),
            kw AS (
              SELECT id, ROW_NUMBER() OVER (
                ORDER BY ts_rank(tsv, q) DESC
              ) AS rnk
              FROM chunks,
                plainto_tsquery(%(qt)s) q
              WHERE acl_tags && %(acl)s
                AND tsv @@ q
              LIMIT 20
            )
            SELECT c.id, c.doc_id, c.section, c.body,
              1.0 / (%(rrf)s + COALESCE(vec.rnk, 999))
              + 1.0 / (%(rrf)s + COALESCE(kw.rnk, 999))
                AS score
            FROM chunks c
            LEFT JOIN vec ON vec.id = c.id
            LEFT JOIN kw ON kw.id = c.id
            WHERE vec.id IS NOT NULL
               OR kw.id IS NOT NULL
            ORDER BY score DESC
            LIMIT %(k)s
            """,
            {"qv": qvec, "qt": query, "acl": acl,
             "rrf": RRF_K, "k": k},
        ).fetchall()
        return [
            {"id": r[0], "doc_id": r[1],
             "section": r[2], "body": r[3]}
            for r in rows
        ]

# index.py (continued) — the Qdrant alternative
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchAny)


class QdrantStore:
    """Drop-in backend once filtered p99 is the pain."""

    def __init__(self, url: str, collection: str):
        self.client = QdrantClient(url=url)
        self.collection = collection

    def hybrid_search(
        self, query: str, k: int = 20,
        acl: list[str] | None = None,
    ) -> list[dict]:
        """Qdrant's native dense + sparse fusion."""
        qvec = embed(query)
        flt = Filter(must=[FieldCondition(
            key="acl_tags",
            match=MatchAny(any=acl or ["public"]))])
        hits = self.client.query_points(
            collection_name=self.collection,
            query=qvec, query_filter=flt,
            limit=k).points
        return [
            {"id": h.id, **h.payload} for h in hits]
