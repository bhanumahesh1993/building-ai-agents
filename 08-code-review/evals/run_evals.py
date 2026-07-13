# evals/run_evals.py
from __future__ import annotations

import json

from review.graph import build_graph

graph = build_graph()


def _confirmed(state: dict) -> list[dict]:
    return [
        v["finding"] for v in state["verified"]
        if v["verdict"] == "confirmed"]


def score_one(case: dict) -> dict:
    cfg = {"configurable":
           {"thread_id": case["pr_id"]}}
    state = graph.invoke(
        {"pr_id": case["pr_id"], "diff": case["diff"]},
        config=cfg)
    found = _confirmed(state)

    if case["clean"]:
        return {
            "pr_id": case["pr_id"],
            "false_positive": len(found) > 0,
        }

    seeded = case["seeded_bugs"]
    hits = 0
    for bug in seeded:
        for f in found:
            near = abs(f["line"] - bug["line"]) <= 2
            if f["path"] == bug["path"] and near:
                hits += 1
                break
    return {
        "pr_id": case["pr_id"],
        "detection_rate": hits / max(len(seeded), 1),
    }


if __name__ == "__main__":
    with open("evals/dataset.jsonl") as fh:
        cases = [json.loads(line) for line in fh]
    results = [score_one(c) for c in cases]
    for r in results:
        print(r)
