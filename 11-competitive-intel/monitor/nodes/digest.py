# monitor/nodes/digest.py
from __future__ import annotations

import os

import anthropic

from ..prompts import DIGEST_SYSTEM
from ..state import MonitorState

DIGEST_MODEL = os.getenv(
    "DIGEST_MODEL", "claude-sonnet-4-5")

_llm: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _llm
    if _llm is None:
        _llm = anthropic.Anthropic()
    return _llm


def digest_node(state: MonitorState) -> dict:
    """Write the grouped, cited digest for this run."""
    cutoff = state.get("min_score", 3)
    survivors = [
        c for c in state.get("scored", [])
        if c["score"] >= cutoff
    ]
    if not survivors:
        return {"digest":
            "No notable competitor changes today."}

    import json
    prompt = DIGEST_SYSTEM.format(
        changes=json.dumps(survivors, indent=2))
    resp = _get_client().messages.create(
        model=DIGEST_MODEL, max_tokens=900,
        messages=[{"role": "user",
                   "content": prompt}],
    )
    return {"digest": resp.content[0].text}
