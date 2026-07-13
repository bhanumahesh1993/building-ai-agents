# evals/run_evals.py
from __future__ import annotations

import json

from langgraph.types import Command

from panel.graph import build_graph
from .judge import grade_reasoning


def _transcript(state: dict) -> str:
    return "\n".join(
        f"round {a['round']} [{a['stance']} -> "
        f"{a['hypothesis']}] {a['text']}"
        for a in state["arguments"])


def run_one(case: dict) -> dict:
    with open(case["vignette_file"]) as fh:
        vignette = fh.read()
    graph = build_graph()
    cfg = {"configurable":
           {"thread_id": case["vignette_file"]}}
    graph.invoke({
        "vignette": vignette,
        "available_results": case["available_results"],
        "max_rounds": 3, "cost_cap": 500.0,
    }, config=cfg)
    state = graph.invoke(
        Command(resume={"reviewed": True}), config=cfg)

    top = state["final_differential"][0]["name"].lower()
    accurate = case["gold_diagnosis"].lower() in top \
        or top in case["gold_diagnosis"].lower()
    caught_bias = bool(state["bias_flags"]) if \
        case["is_bias_trap"] else True
    reasoning = grade_reasoning(_transcript(state))

    return {
        "diagnostic_accuracy": accurate,
        "bias_caught": caught_bias,
        "cost_ok": state["cost_total"] <=
            case["reasonable_cost_ceiling"] * 1.5,
        **reasoning,
    }


if __name__ == "__main__":
    with open("evals/dataset.jsonl") as fh:
        cases = [json.loads(line) for line in fh]
    for case in cases:
        print(case["vignette_file"], run_one(case))
