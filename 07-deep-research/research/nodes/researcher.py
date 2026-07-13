# research/nodes/researcher.py
from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic

from ..prompts import WORKER_SYSTEM
from ..state import WorkerState
from ..tools import web_search, is_trusted

WORKER_MODEL = os.getenv(
    "WORKER_MODEL", "claude-sonnet-4-5")

_llm = ChatAnthropic(
    model=WORKER_MODEL, temperature=0)


def research_node(state: WorkerState) -> dict:
    """One subagent: search, read, and distil."""
    task = state["task"]
    hits = web_search(task["goal"], k=6)
    trusted = [h for h in hits if is_trusted(h["url"])]
    results = trusted or hits          # fall back
    context = "\n\n".join(
        f"[{i}] {r['title']}\n{r['snippet']}\n"
        f"URL: {r['url']}"
        for i, r in enumerate(results)
    )
    prompt = WORKER_SYSTEM.format(
        topic=task["topic"],
        goal=task["goal"],
        context=context,
    )
    resp = _llm.invoke(prompt)
    finding = {
        "topic": task["topic"],
        "summary": resp.content,
        "sources": results,
    }
    return {"findings": [finding]}
