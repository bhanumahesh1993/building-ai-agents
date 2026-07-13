# monitor/nodes/diff.py
from __future__ import annotations

import os

import anthropic
import numpy as np

from ..prompts import DIFF_SYSTEM
from ..state import WorkerState

DIFF_MODEL = os.getenv(
    "DIFF_MODEL", "claude-sonnet-4-5")
# Cosine distance below this = "same meaning."
# Only pages past this gate cost a model call.
DRIFT_THRESHOLD = float(
    os.getenv("DRIFT_THRESHOLD", "0.08"))

_llm: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _llm
    if _llm is None:
        _llm = anthropic.Anthropic()
    return _llm


def _cosine_distance(
        a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    sim = np.dot(va, vb) / (
        np.linalg.norm(va) * np.linalg.norm(vb))
    return float(1.0 - sim)


def diff_node(state: dict) -> dict:
    """Gate on embedding drift, then confirm with a
    cheap read only for pages that moved."""
    result = state["_worker_result"]
    previous = result["previous"]

    if previous is None:
        # First time seeing this page: no prior to
        # diff against, nothing to report yet.
        return {"changes": []}

    distance = _cosine_distance(
        result["embedding"], previous["embedding"])
    if distance < DRIFT_THRESHOLD:
        return {"changes": []}

    prompt = DIFF_SYSTEM.format(
        old_text=previous["text"][:3000],
        new_text=result["text"][:3000],
    )
    resp = _get_client().messages.create(
        model=DIFF_MODEL, max_tokens=300,
        messages=[{"role": "user",
                   "content": prompt}],
    )
    verdict = resp.content[0].text
    changed = "NO_MEANINGFUL_CHANGE" not in verdict

    return {"changes": [{
        "url": result["url"],
        "competitor": result["competitor"],
        "kind": result["kind"],
        "summary": verdict,
        "changed": changed,
        "evidence": result["url"],
    }] if changed else []}
