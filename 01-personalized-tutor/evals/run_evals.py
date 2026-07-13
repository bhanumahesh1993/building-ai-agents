# evals/run_evals.py
from __future__ import annotations

import json

LADDER = ["easy", "medium", "hard"]


def adaptation_ok(events: list[dict]) -> dict:
    """Cheap structural check: does difficulty move the
    right direction after each graded answer?"""
    ok = True
    for e in events:
        before = LADDER.index(e["difficulty_before"])
        after = LADDER.index(e["difficulty_after"])
        if e["next_difficulty"] == "harder" and after < before:
            ok = False
        if e["next_difficulty"] == "easier" and after > before:
            ok = False
    return {"adaptation_monotonic": ok, "n_turns": len(events)}


if __name__ == "__main__":
    with open("evals/trajectories.jsonl") as fh:
        for line in fh:
            print(adaptation_ok(json.loads(line)))
