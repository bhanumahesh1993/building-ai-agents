# firm/nodes/debate.py
from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic

from ..prompts import BEAR_SYSTEM, BULL_SYSTEM
from ..state import FirmState

DEBATE_MODEL = os.getenv(
    "DEBATE_MODEL", "claude-sonnet-4-5")

_llm = ChatAnthropic(model=DEBATE_MODEL, temperature=0.3)


def _transcript(state: FirmState) -> str:
    lines = [
        f"[{t['side'].upper()} r{t['round']}] {t['argument']}"
        for t in state.get("debate", [])
    ]
    return "\n".join(lines) if lines else "(no turns yet)"


def bull_node(state: FirmState) -> dict:
    """The bull researcher argues the long thesis."""
    prompt = BULL_SYSTEM.format(
        symbol=state["symbol"],
        views=state["analyst_views"],
        transcript=_transcript(state),
    )
    resp = _llm.invoke(prompt)
    turn = {
        "round": state.get("debate_round", 0) + 1,
        "side": "bull", "argument": resp.content,
    }
    return {"debate": [turn]}


def bear_node(state: FirmState) -> dict:
    """The bear researcher argues against, then closes the
    round by advancing the round counter."""
    prompt = BEAR_SYSTEM.format(
        symbol=state["symbol"],
        views=state["analyst_views"],
        transcript=_transcript(state),
    )
    resp = _llm.invoke(prompt)
    turn = {
        "round": state.get("debate_round", 0) + 1,
        "side": "bear", "argument": resp.content,
    }
    return {
        "debate": [turn],
        "debate_round": state.get("debate_round", 0) + 1,
    }
