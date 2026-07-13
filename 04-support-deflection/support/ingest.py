# support/ingest.py
"""Load Notewise KB markdown into pgvector + FTS."""
from __future__ import annotations

import pathlib
import re

import psycopg
from pgvector.psycopg import register_vector
from openai import OpenAI

DB_URL = "postgresql://localhost/notewise_kb"
KB_DIR = pathlib.Path("kb")
EMBED_MODEL = "text-embedding-3-small"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS kb_chunks (
    id        bigserial PRIMARY KEY,
    doc       text,
    section   text,
    url       text,
    body      text,
    embedding vector(1536),
    tsv       tsvector GENERATED ALWAYS AS
              (to_tsvector('english', body)) STORED
);
"""


def embed(text: str) -> list[float]:
    resp = _get_client().embeddings.create(
        model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split a KB doc on its own '## ' headings."""
    parts = re.split(r"\n(?=## )", text)
    out = []
    for part in parts:
        lines = part.strip().splitlines()
        if not lines:
            continue
        heading = lines[0].lstrip("#").strip()
        body = "\n".join(lines[1:]).strip()
        if body:
            out.append((heading, body))
    return out


def ingest_file(conn, path: pathlib.Path, url: str):
    """Chunk one KB article by heading, embed, store."""
    doc = path.stem
    text = path.read_text()
    for section, body in split_sections(text):
        conn.execute(
            "INSERT INTO kb_chunks"
            " (doc, section, url, body, embedding)"
            " VALUES (%s, %s, %s, %s, %s)",
            (doc, section, url, body, embed(body)),
        )
    conn.commit()


if __name__ == "__main__":
    with psycopg.connect(DB_URL) as conn:
        register_vector(conn)
        conn.execute(SCHEMA)
        conn.commit()
        for path in KB_DIR.glob("*.md"):
            url = f"https://help.notewise.app/{path.stem}"
            ingest_file(conn, path, url)
            print(f"ingested {path.name}")
