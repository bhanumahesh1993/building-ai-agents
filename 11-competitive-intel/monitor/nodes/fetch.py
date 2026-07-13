# monitor/nodes/fetch.py
from __future__ import annotations

import os
from datetime import datetime, timezone

import anthropic
import psycopg
from psycopg.rows import dict_row

from ..fetch_tool import fetch_page
from ..state import WorkerState

EMBED_MODEL = os.getenv(
    "EMBED_MODEL", "voyage-3.5")

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    """Lazily build the embedding client so the module
    imports without a key present (tests, offline use)."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _get_db_url() -> str:
    """Read the connection string lazily so importing
    this module never requires DATABASE_URL to be set."""
    return os.environ["DATABASE_URL"]


def _embed(text: str) -> list[float]:
    """Embed cleaned page text via the Voyage API."""
    resp = _get_client().embeddings.create(
        model=EMBED_MODEL,
        input=text[:8000],
    )
    return resp.data[0].embedding


def _last_snapshot(url: str) -> dict | None:
    with psycopg.connect(_get_db_url(), row_factory=dict_row) as conn:
        row = conn.execute(
            """SELECT text, embedding FROM snapshots
               WHERE url = %s
               ORDER BY fetched_at DESC LIMIT 1""",
            (url,),
        ).fetchone()
    return row


def _store_snapshot(
        url: str, competitor: str, kind: str,
        text: str, embedding: list[float]) -> None:
    with psycopg.connect(_get_db_url()) as conn:
        conn.execute(
            """INSERT INTO snapshots
               (url, competitor, kind, text,
                embedding, fetched_at)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (url, competitor, kind, text, embedding,
             datetime.now(timezone.utc)),
        )
        conn.commit()


def fetch_node(state: WorkerState) -> dict:
    """One worker: fetch, embed, snapshot one page."""
    text = fetch_page(
        state["url"], state["content_selector"])
    embedding = _embed(text)
    previous = _last_snapshot(state["url"])
    _store_snapshot(
        state["url"], state["competitor"],
        state["kind"], text, embedding)

    return {"_worker_result": {
        "url": state["url"],
        "competitor": state["competitor"],
        "kind": state["kind"],
        "text": text,
        "embedding": embedding,
        "previous": previous,
    }}
