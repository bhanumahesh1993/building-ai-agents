# firm/nodes/manager.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic
from langgraph.types import interrupt

from ..prompts import MANAGER_SYSTEM
from ..state import FirmState

MANAGER_MODEL = os.getenv(
    "MANAGER_MODEL", "claude-opus-4-5")
CONFIRM_ABOVE_PCT = float(
    os.getenv("CONFIRM_ABOVE_PCT", "0.03"))

_llm = ChatAnthropic(model=MANAGER_MODEL, temperature=0)


def manager_node(state: FirmState) -> dict:
    """Final SIMULATED decision. Never places a real order."""
    prompt = MANAGER_SYSTEM.format(
        proposal=state["proposal"], risk=state["risk"])
    resp = _llm.invoke(prompt)
    decision = json.loads(resp.content)

    if not state["risk"]["approved"]:
        # A risk veto is never negotiable, no matter what
        # the manager model tries to output.
        decision = {
            "action": "HOLD", "size_pct": 0.0,
            "rationale": "Risk veto: " + "; ".join(
                state["risk"]["reasons"]),
        }
    elif (decision["action"] != "HOLD"
          and decision["size_pct"] > CONFIRM_ABOVE_PCT):
        # Paper trade above the threshold pauses for a human.
        # Still never a real order — only whether the
        # simulated blotter records the fill.
        ok = interrupt({
            "symbol": state["symbol"], "decision": decision,
        })
        if not ok.get("confirmed", False):
            decision = {
                "action": "HOLD", "size_pct": 0.0,
                "rationale": "Human declined to confirm.",
            }

    fill = {
        "symbol": state["symbol"], "action": decision["action"],
        "size_pct": decision["size_pct"],
        "simulated": True, "broker_order_id": None,
    }
    return {"decision": decision, "paper_fill": fill}
