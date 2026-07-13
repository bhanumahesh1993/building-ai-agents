# evals/run_evals.py
from __future__ import annotations

import json

from aml.scoring import match_typologies


def recall_and_fpr(
    labeled_cases: list[dict],
    detected_ids: set[str],
) -> dict:
    """Deterministic checks -- no judge needed."""
    real = {
        c["case_id"] for c in labeled_cases
        if c["is_real_case"]}
    caught = real & detected_ids
    recall = len(caught) / max(1, len(real))
    opened_not_real = detected_ids - real
    fpr = len(opened_not_real) / max(
        1, len(detected_ids))
    return {"recall": recall, "false_positive_rate": fpr}


def explainability_ok(case) -> bool:
    """Every typology match must cite real evidence."""
    return all(
        len(m.evidence) > 0
        and all(e.txn_ids for e in m.evidence)
        for m in case.typologies)


if __name__ == "__main__":
    with open("evals/labeled_cases.jsonl") as fh:
        cases = [json.loads(line) for line in fh]
    print(recall_and_fpr(cases, detected_ids=set()))
