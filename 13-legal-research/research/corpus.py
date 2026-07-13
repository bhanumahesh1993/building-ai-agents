# research/corpus.py
from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row


def _get_db_url() -> str:
    """Read lazily so the module imports without the
    env var present (tests, offline use)."""
    return os.environ["CASE_DB_URL"]


def _conn():
    return psycopg.connect(_get_db_url(), row_factory=dict_row)


def search_cases(
    query_embedding: list[float],
    jurisdiction: str,
    k: int = 6,
) -> list[dict]:
    """Nearest-neighbor search over case chunks."""
    sql = """
        SELECT case_id, case_name, citation, court,
               year, jurisdiction, chunk_text, status
        FROM case_chunks
        WHERE jurisdiction = %(j)s
        ORDER BY embedding <=> %(q)s::vector
        LIMIT %(k)s
    """
    with _conn() as conn:
        rows = conn.execute(
            sql, {"q": query_embedding,
                  "j": jurisdiction, "k": k},
        ).fetchall()
    return rows


def case_exists(case_id: str) -> dict | None:
    """The Tier-1 check: is this case real, at all?"""
    sql = """
        SELECT case_id, case_name, citation, court,
               year, jurisdiction, status
        FROM cases WHERE case_id = %(id)s
    """
    with _conn() as conn:
        row = conn.execute(
            sql, {"id": case_id}).fetchone()
    return row


def case_full_text(case_id: str) -> str | None:
    """The Tier-2 material: what the case actually says."""
    sql = """
        SELECT string_agg(chunk_text, ' ' ORDER BY seq)
        AS full_text
        FROM case_chunks WHERE case_id = %(id)s
        GROUP BY case_id
    """
    with _conn() as conn:
        row = conn.execute(
            sql, {"id": case_id}).fetchone()
    return row["full_text"] if row else None
