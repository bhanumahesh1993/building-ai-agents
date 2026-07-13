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

_llm = anthropic.Anthropic()


def score_node(state: dict) -> dict:
    """Score one confirmed change for newsworthiness."""
    change: ChangeRecord = state["_change"]
    prompt = SCORE_SYSTEM.format(
        kind=change["kind"],
        summary=change["summary"],
    )
    resp = _llm.messages.create(
        model=SCORE_MODEL, max_tokens=200,
        messages=[{"role": "user",
                   "content": prompt}],
    )
    raw = json.loads(resp.content[0].text)
    base = int(raw["score"])
    weight = KIND_WEIGHT.get(change["kind"], 1.0)
    final = round(min(5, base * weight))

    return {"scored": [{
        "url": change["url"],
        "competitor": change["competitor"],
        "kind": change["kind"],
        "summary": change["summary"],
        "score": final,
        "reason": raw["reason"],
    }]}
