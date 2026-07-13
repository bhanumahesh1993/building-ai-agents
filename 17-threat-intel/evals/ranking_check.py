# evals/ranking_check.py
from __future__ import annotations

import json

from crew.crew import run_weekly_brief


def top_k_overlap(
    predicted: list[str], expert: list[str], k: int = 3,
) -> float:
    """Fraction of the analyst-labeled top-k that our
    ranked list also placed in its top-k. No model call -
    a fact about ordering, not about taste."""
    pred_top = set(predicted[:k])
    expert_top = set(expert[:k])
    return len(pred_top & expert_top) / len(expert_top)


def run_ranking_eval(labels_path: str) -> dict:
    brief = run_weekly_brief(days=7, week_of="eval")
    predicted = [a.split(":")[0].strip()
                 for a in brief.ranked_actions]
    with open(labels_path) as fh:
        expert = json.load(fh)["expert_top_ids"]
    return {
        "top3_overlap": top_k_overlap(predicted, expert),
        "predicted_top3": predicted[:3],
        "expert_top3": expert[:3],
    }
