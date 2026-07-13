# evals/run_evals.py
from __future__ import annotations

import json

from agents import Runner

from shopping.agents import cart_gate, compare_worker
from shopping.agents import concierge, search_worker
from shopping.judge import grade
from shopping.tools import CALLED_TOOLS


def gate_never_bypassed() -> bool:
    """The one check that must never regress."""
    for agent in (
        concierge, search_worker,
        compare_worker, cart_gate,
    ):
        names = {t.name for t in agent.tools}
        if "confirm_order" in names:
            return False
    return "confirm_order" not in CALLED_TOOLS


def run_one(query: dict) -> dict:
    CALLED_TOOLS.clear()
    import asyncio
    result = asyncio.run(
        Runner.run(concierge, query["message"]))
    proposal = result.final_output
    over_budget = (
        query["budget"] is not None
        and gate_never_bypassed()
        and str(query["budget"]) not in proposal
        and "$" in proposal
    )
    scores = grade(query["message"], proposal)
    return {
        **scores,
        "gate_held": gate_never_bypassed(),
        "budget_flag": over_budget,
    }


if __name__ == "__main__":
    with open("evals/dataset.jsonl") as fh:
        for line in fh:
            q = json.loads(line)
            print(q["message"], run_one(q))
