# monitor/nodes/score.py
from __future__ import annotations

import json
import os

import anthropic

from ..prompts import SCORE_SYSTEM
from ..state import ChangeRecord

SCORE_MODEL = os.getenv(
    "SCORE_MODEL", "claude-sonnet-4-5")

# Page kinds carry different baseline weight —
# a pricing change starts more important than a
# careers post, before content is even read.
KIND_WEIGHT = {
    "pricing": 1.3,
    "changelog": 1.1,
    "careers": 0.9,
    "blog": 0.8,
}

_llm: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _llm
    if _llm is None:
        _llm = anthropic.Anthropic()
    return _llm


def compute_final_score(base_score: int, kind: str) -> int:
    """Apply the page-kind weight and clamp to the 1-5
    scale. Pure and deterministic -- no model call --
    so the significance-scoring math is unit-testable
    without live credentials."""
    weight = KIND_WEIGHT.get(kind, 1.0)
    return round(min(5, base_score * weight))


def score_node(state: dict) -> dict:
    """Score one confirmed change for newsworthiness."""
    change: ChangeRecord = state["_change"]
    prompt = SCORE_SYSTEM.format(
        kind=change["kind"],
        summary=change["summary"],
    )
    resp = _get_client().messages.create(
        model=SCORE_MODEL, max_tokens=200,
        messages=[{"role": "user",
                   "content": prompt}],
    )
    raw = json.loads(resp.content[0].text)
    final = compute_final_score(int(raw["score"]), change["kind"])

    return {"scored": [{
        "url": change["url"],
        "competitor": change["competitor"],
        "kind": change["kind"],
        "summary": change["summary"],
        "score": final,
        "reason": raw["reason"],
    }]}
