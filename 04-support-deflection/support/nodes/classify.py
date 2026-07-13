# support/nodes/classify.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..state import TicketState

CLASSIFY_MODEL = os.getenv(
    "CLASSIFY_MODEL", "claude-haiku-4-5")

CATEGORIES = (
    "billing", "account", "how_to",
    "bug", "feature_request", "abuse",
)

_llm = ChatAnthropic(
    model=CLASSIFY_MODEL, temperature=0)

SYSTEM = """Classify this Notewise support message
into exactly one category: {cats}.

"abuse" covers spam, threats, or anything unrelated
to Notewise support. "feature_request" covers ideas
or asks for something the product does not do today.

Return ONLY JSON: {{"category": "...",
"confidence": 0.0-1.0}}

Message: {message}"""


def classify_node(state: TicketState) -> dict:
    """Cheap model: label intent, estimate confidence."""
    prompt = SYSTEM.format(
        cats=", ".join(CATEGORIES),
        message=state["message"],
    )
    resp = _llm.invoke(prompt)
    raw = json.loads(resp.content)
    cat = raw["category"]
    if cat not in CATEGORIES:
        cat = "abuse"
    return {
        "category": cat,
        "confidence": float(raw["confidence"]),
        "events": [
            {"node": "classify", "category": cat}],
    }
