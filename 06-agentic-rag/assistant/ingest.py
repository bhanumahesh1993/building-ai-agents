# ingest.py — chunk, embed, and upsert documents
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

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


@dataclass
class Chunk:
    doc_id: str
    section: str
    body: str
    acl_tags: list[str] = field(
        default_factory=lambda: ["public"])


def embed(text: str) -> list[float]:
    """Turn one string into a 1536-dim vector."""
    resp = _get_client().embeddings.create(
        model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


HEADING = re.compile(r"^(#{1,3})\s+(.+)$", re.M)


def _pack(body: str, budget: int) -> list[str]:
    """Greedily pack sentences to ~budget chars."""
    sentences = re.split(r"(?<=[.!?])\s+", body)
    windows, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) > budget and cur:
            windows.append(cur.strip())
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        windows.append(cur.strip())
    return windows or [body]


def structural_chunks(
    text: str, doc_id: str, budget: int = 900,
) -> list[Chunk]:
    """Split on headings; sentence-fallback if none."""
    marks = list(HEADING.finditer(text))
    if not marks:
        return [
            Chunk(doc_id=doc_id, section="body", body=w)
            for w in _pack(text, budget)
        ]
    bounds = [m.start() for m in marks] + [len(text)]
    out: list[Chunk] = []
    for i, m in enumerate(marks):
        title = m.group(2).strip()
        body = text[m.end():bounds[i + 1]]
        for window in _pack(body.strip(), budget):
            out.append(Chunk(
                doc_id=doc_id, section=title,
                body=f"{title}\n{window}"))
    return out
