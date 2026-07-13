# grading/nodes/similarity.py
from __future__ import annotations

import os

import numpy as np
import psycopg
import voyageai

from ..state import BatchState

EMBED_MODEL = os.getenv("EMBED_MODEL", "voyage-3.5")
FLAG_THRESHOLD = float(
    os.getenv("SIM_THRESHOLD", "0.86"))

_vo: voyageai.Client | None = None


def _get_client() -> voyageai.Client:
    """Lazily build so the module imports without a key present
    (tests, offline use)."""
    global _vo
    if _vo is None:
        _vo = voyageai.Client(
            api_key=os.environ["VOYAGE_API_KEY"])
    return _vo


def _embed(texts: list[str]) -> list[list[float]]:
    resp = _get_client().embed(
        texts, model=EMBED_MODEL, input_type="document")
    return resp.embeddings


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    return float(
        va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb)))


def _corpus_match(
    conn: psycopg.Connection, vector: list[float],
) -> tuple[str | None, float]:
    """Nearest essay in the stored class corpus."""
    row = conn.execute(
        "SELECT essay_id, 1 - (embedding <=> %s::vector) "
        "AS sim FROM class_corpus "
        "ORDER BY embedding <=> %s::vector LIMIT 1",
        (vector, vector),
    ).fetchone()
    return (row[0], row[1]) if row else (None, 0.0)


def similarity_node(state: BatchState) -> dict:
    """Flag close matches for a human — never auto-fail
    an essay, and never call it plagiarism."""
    pending = [
        g for g in state["graded"]
        if g["status"] == "drafted"
    ]
    if not pending:
        return {}
    vectors = _embed([g["text"] for g in pending])
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    updated = []
    for i, g in enumerate(pending):
        best_id, best_sim = _corpus_match(
            conn, vectors[i])
        for j, other in enumerate(pending):
            if other["essay_id"] == g["essay_id"]:
                continue
            sim = _cosine(vectors[i], vectors[j])
            if sim > best_sim:
                best_sim, best_id = sim, other["essay_id"]
        flagged = best_sim >= FLAG_THRESHOLD
        notes = (
            f"{best_sim:.2f} similarity to {best_id} — "
            "worth a look before releasing"
            if flagged else ""
        )
        updated.append({
            **g, "similarity_flag": flagged,
            "similarity_notes": notes,
            "status": "screened",
        })
    conn.close()
    return {"graded": updated}
