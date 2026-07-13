# grading/nodes/review_gate.py
from __future__ import annotations

from langgraph.types import interrupt

from ..state import BatchState


def review_gate_node(state: BatchState) -> dict:
    """Pause the batch for the teacher's sign-off."""
    queue = [
        {"essay_id": g["essay_id"],
         "student_id": g["student_id"],
         "total": g["total"], "scores": g["scores"],
         "feedback": g["feedback"],
         "flagged": g["similarity_flag"],
         "similarity_notes": g["similarity_notes"]}
        for g in state["graded"]
        if g["status"] == "screened"
    ]
    decision = interrupt({"queue": queue})
    approve = set(decision.get("approve", []))
    returned = set(
        decision.get("return_for_rescore", []))
    edits = decision.get("edits", {})

    updated = []
    for g in state["graded"]:
        eid = g["essay_id"]
        if eid in edits:
            g = {**g, **edits[eid]}
        if eid in approve:
            g = {**g, "status": "approved"}
        elif eid in returned:
            g = {**g, "status": "returned"}
        updated.append(g)
    return {"graded": updated,
            "loops": state.get("loops", 0) + 1}
