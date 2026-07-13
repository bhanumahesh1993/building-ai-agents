# triage/nodes/verdict.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..prompts import VERDICT_SYSTEM
from ..state import TriageState

VERDICT_MODEL = os.getenv(
    "VERDICT_MODEL", "claude-opus-4-5")

_llm: ChatAnthropic | None = None


def _get_llm() -> ChatAnthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(
            model=VERDICT_MODEL, temperature=0)
    return _llm


def verdict_node(state: TriageState) -> dict:
    """Reason over the case; no tools, only an opinion.
    The respond node owns the only hands in this graph."""
    findings = "\n\n".join(
        f"[{e['kind']}] {e['summary']}"
        for e in state["enrichment"])
    prompt = VERDICT_SYSTEM.format(
        rule=state["alert"]["rule_name"],
        alert=state["alert"]["raw"],
        findings=findings,
        pattern=state["pattern_notes"],
    )
    resp = _get_llm().invoke(prompt)
    verdict = json.loads(resp.content)
    return {
        "verdict": verdict,
        "audit": [{"node": "verdict",
                    "label": verdict["label"]}],
    }
