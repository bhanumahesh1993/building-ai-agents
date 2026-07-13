# firm/nodes/risk.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..data import portfolio_snapshot
from ..prompts import RISK_SYSTEM
from ..state import FirmState

RISK_MODEL = os.getenv("RISK_MODEL", "claude-sonnet-4-5")
POSITION_CAP = float(os.getenv("POSITION_CAP_PCT", "0.05"))
DRAWDOWN_LIMIT = float(
    os.getenv("DRAWDOWN_LIMIT_PCT", "0.15"))
PAPER_CAPITAL = float(
    os.getenv("PAPER_CAPITAL_USD", "100000"))

_llm = ChatAnthropic(model=RISK_MODEL, temperature=0)


def risk_node(state: FirmState) -> dict:
    """The veto team: position sizing + drawdown limit."""
    portfolio = portfolio_snapshot(PAPER_CAPITAL)
    prompt = RISK_SYSTEM.format(
        position_cap=POSITION_CAP,
        drawdown_limit=DRAWDOWN_LIMIT,
        proposal=state["proposal"], portfolio=portfolio,
    )
    resp = _llm.invoke(prompt)
    parsed = json.loads(resp.content)
    # Hard-coded backstop: never trust the model's own
    # arithmetic for the cap. Code enforces it; the LLM
    # only explains the reasoning behind the verdict.
    size = min(
        float(parsed["adjusted_size_pct"]), POSITION_CAP)
    approved = bool(parsed["approved"]) and size > 0
    revisions = state.get("risk_revisions", 0)
    if not approved:
        revisions += 1
    verdict = {
        "approved": approved, "adjusted_size_pct": size,
        "reasons": parsed["reasons"],
    }
    return {"risk": verdict, "risk_revisions": revisions}
