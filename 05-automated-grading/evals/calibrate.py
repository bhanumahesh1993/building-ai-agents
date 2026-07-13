# evals/calibrate.py
from __future__ import annotations

import json
from statistics import mean

from grading.nodes.score import _score_one

TOLERANCE = 1  # points; within this counts as agreement


def _load(path: str) -> list[dict]:
    with open(path) as fh:
        return json.load(fh)


def calibrate(path: str = "evals/golden.json") -> dict:
    rows = _load(path)
    diffs, hits = [], 0
    for row in rows:
        result = _score_one(row["prompt"], row["essay"])
        model_total = sum(
            s["points"] for s in result["scores"])
        diff = abs(model_total - row["teacher_total"])
        diffs.append(diff)
        hits += diff <= TOLERANCE
    return {"n": len(rows),
            "mean_abs_error": round(mean(diffs), 2),
            "agreement_rate": round(hits / len(rows), 2)}


if __name__ == "__main__":
    report = calibrate()
    print(report)
    assert report["agreement_rate"] >= 0.8, (
        "Grader has drifted from teacher calibration")
