# evals/run_evals.py
from __future__ import annotations

import json

from monitor.nodes.diff import _cosine_distance
from monitor.nodes.fetch import _embed


def change_detection_metrics(path: str) -> dict:
    """Precision/recall of the drift gate against
    seeded, human-labeled page pairs."""
    tp = fp = fn = tn = 0
    with open(path) as fh:
        for line in fh:
            row = json.loads(line)
            old_emb = _embed(row["old"])
            new_emb = _embed(row["new"])
            distance = _cosine_distance(
                old_emb, new_emb)
            flagged = distance >= 0.08
            truth = row["meaningfully_changed"]
            if flagged and truth:
                tp += 1
            elif flagged and not truth:
                fp += 1
            elif not flagged and truth:
                fn += 1
            else:
                tn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    false_alarm_rate = (
        fp / (fp + tn) if fp + tn else 0.0)
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "false_alarm_rate": round(
            false_alarm_rate, 3),
    }


if __name__ == "__main__":
    print(change_detection_metrics(
        "evals/seeded_changes.jsonl"))

# evals/run_evals.py (continued)

def significance_calibration(
        path: str, scorer) -> dict:
    """Mean absolute error between the model's score
    and a human-labeled ground truth score."""
    errors = []
    with open(path) as fh:
        for line in fh:
            row = json.loads(line)
            if not row["meaningfully_changed"]:
                continue
            predicted = scorer(row)
            errors.append(
                abs(predicted - row["human_score"]))
    mae = sum(errors) / len(errors) if errors else 0.0
    return {"mean_absolute_error": round(mae, 2)}
