# evals/run_evals.py
from __future__ import annotations

import json

from langgraph.types import Command

from research.graph import build_graph
from research.judge import grade


def trajectory_ok(state: dict) -> dict:
    """Cheap structural checks on a run."""
    topics = {f["topic"] for f in state["findings"]}
    n_sources = sum(
        len(f["sources"]) for f in state["findings"])
    return {
        "worker_count": len(topics),
        "source_count": n_sources,
        "enough_workers": len(topics) >= 2,
        "enough_sources": n_sources >= 4,
    }


def run_one(question: str) -> dict:
    graph = build_graph()
    cfg = {"configurable":
           {"thread_id": question[:24]}}
    graph.invoke(
        {"question": question, "max_loops": 2},
        config=cfg)
    # Auto-approve the plan for the eval run.
    state = graph.invoke(
        Command(resume={"approved": True}),
        config=cfg)
    scores = grade(question, state["report"])
    return {**trajectory_ok(state), **scores}


if __name__ == "__main__":
    with open("evals/dataset.jsonl") as fh:
        for line in fh:
            q = json.loads(line)["question"]
            print(q, run_one(q))
