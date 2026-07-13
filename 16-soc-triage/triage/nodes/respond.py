# triage/nodes/respond.py
from __future__ import annotations

import asyncio

from langgraph.types import interrupt

from ..state import TriageState
from .enrich import SIEM, _call

DESTRUCTIVE = {"disable_account", "isolate_host"}


def respond_node(state: TriageState) -> dict:
    """Auto-resolve read-only outcomes; always pause
    for a human before any state-changing action."""
    v = state["verdict"]
    action = v["recommended_action"]
    alert_id = state["alert"]["alert_id"]

    if action not in DESTRUCTIVE:
        resolution = (
            "closed_fp" if v["label"] == "false_positive"
            else "escalated")
        return {
            "resolution": resolution,
            "action_result": f"no containment ({action})",
            "audit": [{"node": "respond",
                        "action": action, "auto": True}],
        }

    decision = interrupt({
        "alert_id": alert_id,
        "verdict": v,
        "action": action,
    })
    if not decision.get("approved", False):
        return {
            "resolution": "escalated",
            "action_result": "containment declined",
            "audit": [{"node": "respond",
                        "action": action,
                        "approved": False}],
        }

    ent = state["alert"]["entities"]
    if action == "disable_account":
        arg = {"user_id": ent.get("user", ""),
               "ticket_id": alert_id}
    else:
        arg = {"host_id": ent.get("host", ""),
               "ticket_id": alert_id}
    result = asyncio.run(_call(SIEM, action, arg))

    return {
        "resolution": "contained",
        "action_result": result,
        "audit": [{"node": "respond", "action": action,
                    "approved": True}],
    }
