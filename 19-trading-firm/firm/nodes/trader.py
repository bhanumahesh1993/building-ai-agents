# firm/nodes/trader.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..prompts import TRADER_SYSTEM
from ..state import FirmState

TRADER_MODEL = os.getenv(
    "TRADER_MODEL", "claude-opus-4-5")

_llm: ChatAnthropic | None = None


def _get_llm() -> ChatAnthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(
            model=TRADER_MODEL, temperature=0.1)
    return _llm


def trader_node(state: FirmState) -> dict:
    """Propose ONE simulated trade from the debate transcript."""
    lines = [
        f"[{t['side'].upper()} r{t['round']}] {t['argument']}"
        for t in state["debate"]
    ]
    prompt = TRADER_SYSTEM.format(
        symbol=state["symbol"], transcript="\n".join(lines))
    resp = _get_llm().invoke(prompt)
    parsed = json.loads(resp.content)
    proposal = {
        "action": parsed["action"],
        "size_pct": float(parsed["size_pct"]),
        "stop_loss_pct": float(parsed["stop_loss_pct"]),
        "thesis": parsed["thesis"],
    }
    return {"proposal": proposal}
