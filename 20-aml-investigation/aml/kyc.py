# aml/kyc.py
from __future__ import annotations

import os

import psycopg
from openai import OpenAI

from .state import Entity

EMBED_MODEL = os.getenv(
    "EMBED_MODEL", "text-embedding-3-small")
MATCH_THRESHOLD = 0.86  # cosine similarity, not distance

HIGH_RISK_JURISDICTIONS = {
    "offshore-a", "offshore-b", "shell-haven",
}

# The embedding client is constructed lazily behind _get_client() so
# importing this module never requires OPENAI_API_KEY to be set.
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Lazily build so the module imports without a key present."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _embed(text: str) -> str:
    """Embed text; return pgvector's bracketed format."""
    resp = _get_client().embeddings.create(
        model=EMBED_MODEL, input=text)
    vec = resp.data[0].embedding
    return "[" + ",".join(str(v) for v in vec) + "]"


def resolve_entity(
    conn: psycopg.Connection,
    name: str,
    jurisdiction: str,
) -> Entity:
    """Match `name` to a known entity, or mint a new one."""
    qvec = _embed(name)
    row = conn.execute(
        """
        SELECT entity_id, display_name, aliases,
               1 - (embedding <=> %s) AS similarity
        FROM kyc_entities
        ORDER BY embedding <=> %s
        LIMIT 1
        """,
        (qvec, qvec),
    ).fetchone()

    if row and row[3] >= MATCH_THRESHOLD:
        entity_id, display, aliases, _ = row
        if name not in aliases:
            aliases = aliases + [name]
            conn.execute(
                "UPDATE kyc_entities SET aliases = %s "
                "WHERE entity_id = %s",
                (aliases, entity_id),
            )
        return Entity(
            entity_id, display, aliases,
            _risk_tier(jurisdiction))

    entity_id = f"ent_{abs(hash(name)) % 10_000_000}"
    conn.execute(
        "INSERT INTO kyc_entities "
        "(entity_id, display_name, aliases, embedding) "
        "VALUES (%s, %s, %s, %s)",
        (entity_id, name, [name], qvec),
    )
    return Entity(
        entity_id, name, [name], _risk_tier(jurisdiction))


def _risk_tier(jurisdiction: str) -> str:
    if jurisdiction.lower() in HIGH_RISK_JURISDICTIONS:
        return "high"
    if jurisdiction == "unknown":
        return "medium"
    return "low"
