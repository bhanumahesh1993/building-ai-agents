# panel/nodes/steward.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..prompts import STEWARD_SYSTEM
from ..state import PanelState

STEWARD_MODEL = os.getenv(
    "STEWARD_MODEL", "claude-sonnet-4-5")

_llm = ChatAnthropic(model=STEWARD_MODEL, temperature=0)


def steward_node(state: PanelState) -> dict:
    """Report cost-appropriateness; never order or decide."""
    orders_text = "\n".join(
        f"- {o['test']} (${o['cost_usd']:.0f}): "
        f"{o['rationale']}" for o in state["orders"])
    prompt = STEWARD_SYSTEM.format(
        orders=orders_text or "none ordered",
        spent=state["cost_total"], cap=state["cost_cap"])
    resp = _llm.invoke(prompt)
    note = json.loads(resp.content).get(
        "note", resp.content)

    active = sorted(
        (h for h in state["hypotheses"]
         if h["status"] == "active"),
        key=lambda h: -h["confidence"])
    return {
        "final_differential": active[:3],
        "cost_note": note,
    }
