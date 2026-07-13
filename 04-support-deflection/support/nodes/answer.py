# support/nodes/answer.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..state import TicketState

ANSWER_MODEL = os.getenv(
    "ANSWER_MODEL", "claude-sonnet-4-5")

_llm = ChatAnthropic(
    model=ANSWER_MODEL, temperature=0)

SYSTEM = """You are Notewise's tier-1 support agent.
Answer the customer using ONLY the numbered KB
passages below. Cite every claim like [1]. If the
passages do not fully answer the question, set
"grounded" to false instead of guessing — never
invent a policy, price, or feature.

Return ONLY JSON: {{"answer": "...",
"citations": ["1", "3"], "grounded": true}}

Customer message: {message}

KB passages:
{context}"""


def _format_context(hits: list[dict]) -> str:
    lines = []
    for i, h in enumerate(hits, start=1):
        lines.append(
            f"[{i}] ({h['doc']} · {h['section']})"
            f"\n{h['body']}")
    return "\n\n".join(lines)


def answer_node(state: TicketState) -> dict:
    """Answer strictly from KB hits, or refuse."""
    hits = state.get("kb_hits", [])
    if not hits:
        return {
            "grounded": False,
            "events": [{"node": "answer",
                        "grounded": False}],
        }
    prompt = SYSTEM.format(
        message=state["message"],
        context=_format_context(hits),
    )
    resp = _llm.invoke(prompt)
    raw = json.loads(resp.content)
    urls = [
        hits[int(n) - 1]["url"]
        for n in raw.get("citations", [])
        if n.isdigit() and int(n) <= len(hits)
    ]
    return {
        "answer": raw["answer"],
        "citations": urls,
        "grounded": bool(raw["grounded"]),
        "events": [{"node": "answer",
                    "grounded": bool(raw["grounded"])}],
    }
