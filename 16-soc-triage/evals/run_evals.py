# evals/run_evals.py
from __future__ import annotations

import json

from langgraph.types import Command

from triage.graph import build_graph


def run_one(record: dict) -> dict:
    graph = build_graph()
    cfg = {"configurable":
           {"thread_id": record["alert_id"]}}
    graph.invoke(
        {"raw_event": {
            "alert_id": record["alert_id"],
            "rule_name": record["rule_name"],
            "raw": record["raw"]}},
        config=cfg)
    # Auto-approve any gate for the eval run.
    state = graph.invoke(
        Command(resume={"approved": True}),
        config=cfg)
    v = state["verdict"]
    return {
        "alert_id": record["alert_id"],
        "predicted": v["label"],
        "true_label": record["true_label"],
        "n_enriched": len(state["enrichment"]),
        "resolution": state["resolution"],
    }


def score(rows: list[dict]) -> dict:
    n = len(rows)
    correct = sum(
        r["predicted"] == r["true_label"] for r in rows)
    actual_pos = [
        r for r in rows
        if r["true_label"] == "true_positive"]
    missed = [
        r for r in actual_pos
        if r["predicted"] != "true_positive"]
    complete = sum(
        r["n_enriched"] == 3 for r in rows)
    auto_closed = sum(
        r["resolution"] == "closed_fp" for r in rows)
    return {
        "accuracy": correct / n,
        "false_negative_rate": (
            len(missed) / len(actual_pos)
            if actual_pos else 0.0),
        "enrichment_completeness": complete / n,
        "fatigue_reduction_proxy": auto_closed / n,
    }


if __name__ == "__main__":
    rows = []
    with open("evals/dataset.jsonl") as fh:
        for line in fh:
            rows.append(run_one(json.loads(line)))
    print(score(rows))
