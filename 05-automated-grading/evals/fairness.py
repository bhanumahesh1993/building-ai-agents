# evals/fairness.py
from __future__ import annotations

from grading.nodes.score import _score_one


def content_subscore(result: dict) -> int:
    """Total minus Writing Mechanics — isolates the
    argument from the polish of the prose."""
    return sum(
        s["points"] for s in result["scores"]
        if s["criterion"] != "Writing Mechanics")


def fairness_gap(
    pairs: list[tuple[dict, dict]],
) -> list[dict]:
    """Compare content subscores across pairs of essays
    that argue the same point in different registers."""
    out = []
    for a, b in pairs:
        ra = _score_one(a["prompt"], a["essay"])
        rb = _score_one(b["prompt"], b["essay"])
        gap = abs(
            content_subscore(ra) - content_subscore(rb))
        out.append({"pair": (a["id"], b["id"]),
                    "gap": gap})
    return out
