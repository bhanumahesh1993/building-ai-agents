# panel/nodes/analyze.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..prompts import ANALYZE_SYSTEM
from ..state import PanelState

ANALYZE_MODEL = os.getenv(
    "ANALYZE_MODEL", "claude-sonnet-4-5")

_llm = ChatAnthropic(
    model=ANALYZE_MODEL, temperature=0.2)


def analyze_node(state: PanelState) -> dict:
    """Seed the debate with an initial differential."""
    findings = "\n".join(
        f"- {f}" for f in state["findings"])
    prompt = ANALYZE_SYSTEM.format(findings=findings)
    resp = _llm.invoke(prompt)
    data = json.loads(resp.content)
    hyps = [
        {"name": h["name"], "rationale": h["rationale"],
         "confidence": h["confidence"],
         "status": "active"}
        for h in data["hypotheses"][:5]
    ]
    return {"hypotheses": hyps}
