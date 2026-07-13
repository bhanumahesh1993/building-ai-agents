# aml/scoring.py
from __future__ import annotations

from .state import Alert, Case, Evidence, TypologyMatch

TYPOLOGY_WEIGHTS = {
    "structuring": 0.55,
    "layering": 0.65,
    "anomaly": 0.30,
}


def match_typologies(
    alerts: list[Alert],
) -> list[TypologyMatch]:
    """Map fired rules onto named typologies, each
    backed by the transaction ids that triggered it."""
    matches = []
    for rule, weight in TYPOLOGY_WEIGHTS.items():
        hits = [a for a in alerts if a.rule == rule]
        if not hits:
            continue
        source = "anomaly" if rule == "anomaly" else "rule"
        evidence = [
            Evidence(
                claim=a.reason, txn_ids=a.txn_ids,
                source=source)
            for a in hits
        ]
        confidence = min(
            0.95, weight + 0.1 * (len(hits) - 1))
        matches.append(TypologyMatch(
            name=rule, confidence=confidence,
            evidence=evidence))
    return matches


def score_case(case: Case) -> float:
    """A transparent, additive score -- every point on
    the scale traces back to a named typology match."""
    if not case.typologies:
        return 0.0
    raw = sum(
        m.confidence * TYPOLOGY_WEIGHTS.get(m.name, 0.4)
        for m in case.typologies)
    score = min(100.0, raw * 100)
    case.log(
        f"risk_score={score:.1f} from "
        f"{len(case.typologies)} typology match(es)")
    return score
