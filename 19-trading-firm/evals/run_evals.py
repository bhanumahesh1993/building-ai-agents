# evals/run_evals.py
from __future__ import annotations

import json

from evals.judge import grade
from firm.graph import build_graph

POSITION_CAP = 0.05


def trajectory_ok(state: dict) -> dict:
    """Cheap structural checks — no model call needed."""
    sides = {t["side"] for t in state["debate"]}
    size = state["paper_fill"]["size_pct"]
    return {
        "both_sides_spoke": sides == {"bull", "bear"},
        "size_within_cap": size <= POSITION_CAP + 1e-9,
        "veto_respected": (
            state["risk"]["approved"]
            or state["paper_fill"]["action"] == "HOLD"
        ),
    }


def run_one(symbol: str, as_of: str) -> dict:
    graph = build_graph()
    cfg = {"configurable": {"thread_id": f"{symbol}-{as_of}"}}
    state = graph.invoke({
        "symbol": symbol, "as_of": as_of,
        "debate_round": 0, "max_debate_rounds": 2,
        "risk_revisions": 0, "max_risk_revisions": 1,
    }, config=cfg)
    scores = grade(state)
    return {**trajectory_ok(state), **scores}


if __name__ == "__main__":
    with open("evals/dataset.jsonl") as fh:
        for line in fh:
            row = json.loads(line)
            out = run_one(row["symbol"], row["as_of"])
            print(row, out)
