# evals/run_evals.py
from __future__ import annotations

import json
import time

from langgraph.types import Command

from copilot.graph import build_graph


def run_one(record: dict) -> dict:
    graph = build_graph()
    cfg = {"configurable":
           {"thread_id": record["alert_id"]}}
    t0 = time.monotonic()
    graph.invoke(
        {"raw_event": {
            "alert_id": record["alert_id"],
            "service": record["service"],
            "signal": record["signal"],
            "raw": record["raw"]}},
        config=cfg)
    time_to_hyp = time.monotonic() - t0
    # Auto-approve any gate for the eval run.
    state = graph.invoke(
        Command(resume={"approved": True}),
        config=cfg)
    rc = state["root_cause"]
    rem = state["remediation"]
    return {
        "alert_id": record["alert_id"],
        "predicted_category": rc["category"],
        "true_category": record["true_category"],
        "action": rem["action"],
        "needed_action": record["needed_action"],
        "time_to_hypothesis_s": round(
            time_to_hyp, 2),
    }


def score(rows: list[dict]) -> dict:
    n = len(rows)
    correct = sum(
        r["predicted_category"] == r["true_category"]
        for r in rows)
    action_ok = sum(
        r["action"] == r["needed_action"]
        for r in rows)
    no_action_needed = [
        r for r in rows
        if r["needed_action"] == "notify_only"]
    false_remediation = [
        r for r in no_action_needed
        if r["action"] != "notify_only"]
    avg_time = sum(
        r["time_to_hypothesis_s"]
        for r in rows) / n
    return {
        "root_cause_accuracy": correct / n,
        "remediation_appropriateness":
            action_ok / n,
        "avg_time_to_hypothesis_s": round(
            avg_time, 2),
        "false_remediation_rate": (
            len(false_remediation)
            / len(no_action_needed)
            if no_action_needed else 0.0),
    }


if __name__ == "__main__":
    rows = []
    with open("evals/dataset.jsonl") as fh:
        for line in fh:
            rows.append(run_one(json.loads(line)))
    print(score(rows))
