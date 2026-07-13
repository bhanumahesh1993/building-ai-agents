# evals/run_evals.py
from __future__ import annotations

import json

from a2a_client import can_fulfill, delegate, discover
from shared.schemas import ReorderRequest

PROCUREMENT_URL = "http://localhost:8001"


def eval_completion(sku: str, qty: int) -> dict:
    card = discover(PROCUREMENT_URL)
    ok = can_fulfill(card, "fulfill_reorder")
    req = ReorderRequest(
        sku=sku, quantity=qty, spend_cap=5000.0,
        buyer_org="northwind")
    task = delegate(card, req)
    state = task["status"]["state"]
    return {
        "skill_advertised": ok,
        "reached_terminal_or_pause": state in (
            "completed", "input-required", "failed"),
        "state": state,
    }


def eval_negotiation(quotes: list[dict],
                      max_lead: int, po: dict) -> dict:
    """Was the cheapest *eligible* vendor chosen?"""
    eligible = [
        q for q in quotes
        if q["lead_time_days"] <= max_lead]
    best = min(eligible, key=lambda q: q["unit_price"])
    return {"correct": po["supplier"] == best["supplier"]}


def eval_boundary_integrity(
        validator, poisoned_artifact: str) -> dict:
    """A malformed artifact must be rejected, not run."""
    accepted = validator(poisoned_artifact)
    return {"rejected_malformed": not accepted}


if __name__ == "__main__":
    print(json.dumps(
        eval_completion("GASKET-9", 500), indent=2))
