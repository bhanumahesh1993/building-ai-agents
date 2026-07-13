# tests/test_escalation_precision.py
from __future__ import annotations

from support.evals.run_evals import escalation_precision


def test_perfect_routing_scores_1_0():
    rows = [
        {"expect_escalate": True, "escalated": True},
        {"expect_escalate": False, "escalated": False},
    ]
    result = escalation_precision(rows)
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["wrong_deflections"] == 0


def test_wrong_deflection_hurts_recall_not_precision():
    # A ticket that should have escalated but didn't: the
    # dangerous kind of miss (a confident wrong answer shipped
    # instead of being routed to a human).
    rows = [
        {"expect_escalate": True, "escalated": False},
        {"expect_escalate": False, "escalated": False},
    ]
    result = escalation_precision(rows)
    assert result["recall"] == 0.0
    assert result["wrong_deflections"] == 1
    assert result["precision"] == 1.0  # no escalations were made at all


def test_over_escalation_hurts_precision_not_recall():
    rows = [
        {"expect_escalate": False, "escalated": True},
        {"expect_escalate": True, "escalated": True},
    ]
    result = escalation_precision(rows)
    assert result["precision"] == 0.5
    assert result["recall"] == 1.0
    assert result["wrong_deflections"] == 0


def test_empty_rows_defaults_to_perfect_score():
    result = escalation_precision([])
    assert result == {
        "precision": 1.0, "recall": 1.0, "wrong_deflections": 0}
