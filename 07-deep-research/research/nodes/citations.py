# research/nodes/citations.py
from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic

from ..prompts import CITE_SYSTEM
from ..state import ReportState

LEAD_MODEL = os.getenv("LEAD_MODEL", "claude-opus-4-5")

_llm = ChatAnthropic(model=LEAD_MODEL, temperature=0)


def _source_table(state: ReportState) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    n = 1
    for f in state["findings"]:
        for s in f["sources"]:
            url = s["url"]
            if url in seen:
                continue
            seen.add(url)
            lines.append(
                f"[{n}] {s['title']} — {url}")
            n += 1
    return "\n".join(lines)


def cite_node(state: ReportState) -> dict:
    """Separate pass: verify and attach citations."""
    sources = _source_table(state)
    prompt = CITE_SYSTEM.format(
        draft=state["draft"],
        sources=sources,
    )
    resp = _llm.invoke(prompt)
    report = (
        resp.content
        + "\n\n## Sources\n"
        + sources
    )
    return {"report": report}
