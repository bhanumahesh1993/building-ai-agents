# research/nodes/planner.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic
from langgraph.types import interrupt

from ..prompts import PLANNER_SYSTEM
from ..state import ReportState

LEAD_MODEL = os.getenv("LEAD_MODEL", "claude-opus-4-5")
MAX_WORKERS = 4

_llm = ChatAnthropic(model=LEAD_MODEL, temperature=0)


def plan_node(state: ReportState) -> dict:
    """Lead agent: decompose, then pause for a human."""
    prompt = PLANNER_SYSTEM.format(
        question=state["question"],
        max_workers=MAX_WORKERS,
    )
    resp = _llm.invoke(prompt)
    raw = json.loads(resp.content)
    plan = [
        {"topic": t["topic"], "goal": t["goal"]}
        for t in raw["tasks"][:MAX_WORKERS]
    ]
    # Human-in-the-loop: pause for plan approval.
    decision = interrupt({
        "question": state["question"],
        "plan": plan,
    })
    approved = decision.get("approved", True)
    edited = decision.get("plan", plan)
    return {
        "plan": edited if approved else plan,
        "approved": approved,
        "loops": 0,
        "max_loops": state.get("max_loops", 2),
    }
