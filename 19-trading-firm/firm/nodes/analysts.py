# firm/nodes/analysts.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..data import get_fundamentals, get_news, get_ohlcv
from ..prompts import ANALYST_SYSTEM
from ..state import AnalystState

ANALYST_MODEL = os.getenv(
    "ANALYST_MODEL", "claude-sonnet-4-5")

_llm: ChatAnthropic | None = None


def _get_llm() -> ChatAnthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(
            model=ANALYST_MODEL, temperature=0)
    return _llm


_PAYLOAD = {
    "fundamental": lambda sym, d: get_fundamentals(sym, d),
    "technical": lambda sym, d: get_ohlcv(sym, d, 20),
    "sentiment": lambda sym, d: get_news(sym, d),
    "news": lambda sym, d: get_news(sym, d),
}


def analyst_node(state: AnalystState) -> dict:
    """One analyst: read its slice of data, form a view.
    Four of these run in parallel — one per `kind`."""
    kind = state["kind"]
    symbol = state["symbol"]
    as_of = state["as_of"]
    payload = _PAYLOAD[kind](symbol, as_of)
    prompt = ANALYST_SYSTEM[kind].format(
        symbol=symbol, payload=json.dumps(payload))
    resp = _get_llm().invoke(prompt)
    parsed = json.loads(resp.content)
    view = {
        "kind": kind,
        "stance": parsed["stance"],
        "confidence": float(parsed["confidence"]),
        "rationale": parsed["rationale"],
    }
    return {"analyst_views": [view]}
