# support/evals/run_evals.py
from __future__ import annotations

import json
import uuid

from langgraph.types import Command

from ..graph import build_graph
from .judge import grade


def run_one(case: dict) -> dict:
    graph = build_graph()
    thread_id = str(uuid.uuid4())
    cfg = {"configurable": {"thread_id": thread_id}}
    state = graph.invoke(
        {"customer_id": "eval-user",
         "message": case["message"]}, config=cfg)

    if "__interrupt__" in state:
        # Auto-approve the drafted summary in eval runs.
        pending = state["__interrupt__"][0].value
        state = graph.invoke(
            Command(resume={
                "summary": pending["summary"]}),
            config=cfg)

    escalated = state["resolution"] == "escalated"
    row = {
        "message": case["message"],
        "expect_escalate": case["expect_escalate"],
        "escalated": escalated,
        "correct_route": (
            escalated == case["expect_escalate"]),
    }
    if not escalated:
        row.update(grade(
            case["message"], state["answer"],
            state.get("citations", [])))
    return row


def escalation_precision(rows: list[dict]) -> dict:
    """Precision/recall on the should-escalate call."""
    tp = sum(
        1 for r in rows
        if r["expect_escalate"] and r["escalated"])
    fp = sum(
        1 for r in rows
        if not r["expect_escalate"] and r["escalated"])
    fn = sum(
        1 for r in rows
        if r["expect_escalate"] and not r["escalated"])
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    return {
        "precision": precision, "recall": recall,
        "wrong_deflections": fn,
    }


if __name__ == "__main__":
    rows = []
    with open("evals/dataset.jsonl") as fh:
        for line in fh:
            rows.append(run_one(json.loads(line)))
    for r in rows:
        print(r)
    print("---")
    print(escalation_precision(rows))
