# review/nodes/gate.py
from __future__ import annotations

from ..github_stub import post_check
from ..state import ReviewState

BLOCKING = {"critical", "high"}


def gate_node(state: ReviewState) -> dict:
    """Decide block vs approve, post the check."""
    confirmed = [
        v for v in state["verified"]
        if v["verdict"] == "confirmed"]
    blocking = [
        v for v in confirmed
        if v["finding"]["severity"] in BLOCKING]

    if blocking:
        decision, conclusion = "block", "failure"
        title = "Blocking issues found"
    else:
        decision = "approve_with_comments"
        conclusion, title = "neutral", "Reviewed"

    post_check(
        pr_id=state["pr_id"], conclusion=conclusion,
        title=title, summary=state["report"])
    return {"decision": decision}
