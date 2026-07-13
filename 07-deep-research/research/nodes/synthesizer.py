# research/nodes/synthesizer.py
from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic

from ..prompts import SYNTH_SYSTEM
from ..state import ReportState

LEAD_MODEL = os.getenv("LEAD_MODEL", "claude-opus-4-5")

_llm = ChatAnthropic(
    model=LEAD_MODEL, temperature=0.2)


def synthesize_node(state: ReportState) -> dict:
    """Lead agent writes one coherent draft."""
    blocks = []
    for f in state["findings"]:
        blocks.append(f"## {f['topic']}\n{f['summary']}")
    body = "\n\n".join(blocks)
    prompt = SYNTH_SYSTEM.format(
        question=state["question"],
        findings=body,
    )
    resp = _llm.invoke(prompt)
    loops = state.get("loops", 0) + 1
    return {"draft": resp.content, "loops": loops}
