# evals/metrics.py
from __future__ import annotations


def clause_metrics(
    predicted: list[dict], gold: list[dict],
) -> dict:
    """Recall/precision on (contract_id, clause_type)."""
    pred_set = {
        (c["contract_id"], c["clause_type"])
        for c in predicted}
    gold_set = {
        (g["contract_id"], g["clause_type"])
        for g in gold}
    tp = len(pred_set & gold_set)
    recall = tp / len(gold_set) if gold_set else 1.0
    precision = tp / len(pred_set) if pred_set else 1.0
    return {"recall": recall, "precision": precision}


def flag_agreement(
    flags: list[dict], attorney_labels: dict[str, str],
) -> float:
    """Share of flags matching the attorney's severity."""
    if not flags:
        return 1.0
    hits = sum(
        1 for f in flags
        if attorney_labels.get(f["clause_id"])
        == f["severity"])
    return hits / len(flags)


def citation_to_source(
    flags: list[dict], clauses_by_id: dict[str, str],
) -> float:
    """Share of flags whose quote is a real substring."""
    if not flags:
        return 1.0
    def norm(s): return " ".join(s.split()).lower()
    hits = sum(
        1 for f in flags
        if norm(f["quote"])
        in norm(clauses_by_id.get(f["clause_id"], "")))
    return hits / len(flags)
