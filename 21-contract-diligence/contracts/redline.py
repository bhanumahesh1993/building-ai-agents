# contracts/redline.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from .state import DDState, Redline

LEAD_MODEL = os.getenv("LEAD_MODEL", "claude-opus-4-5")

REDLINE_SYSTEM = """You are drafting redline
suggestions for a due-diligence review. For each
grounded flag below, propose replacement language
that would resolve the concern, anchored to the
playbook position cited. Do not invent new clause
types and do not address clauses not listed here.

Grounded flags:
{flags}

Return ONLY JSON:
{{"redlines": [
  {{"clause_id": "...", "proposed_text": "...",
    "rationale": "why this resolves the concern"}}
]}}"""

_llm = ChatAnthropic(model=LEAD_MODEL, temperature=0.2)


def redline_node(state: DDState) -> dict:
    """Lead agent drafts one redline per grounded flag."""
    grounded = state.get("grounded", [])
    if not grounded:
        return {"redlines": []}
    body = "\n\n".join(
        f"[{g['clause_id']}] quote: {g['quote']}\n"
        f"deviation: {g['deviation']} ref: "
        f"{g['playbook_ref']}\nwhy: {g['rationale']}"
        for g in grounded)
    prompt = REDLINE_SYSTEM.format(flags=body)
    resp = _llm.invoke(prompt)
    parsed = json.loads(resp.content)
    redlines: list[Redline] = [{
        "clause_id": r["clause_id"],
        "proposed_text": r["proposed_text"],
        "rationale": r["rationale"],
    } for r in parsed["redlines"]]
    return {"redlines": redlines}
