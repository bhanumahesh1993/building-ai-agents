# tests/test_typology_matching.py — deterministic checks for the
# monitor's rule/anomaly detectors and the scoring layer that maps
# fired alerts onto named typologies. These are plain functions with
# no model call, so they are exercised directly against
# aml/monitor.py and aml/scoring.py. A recurring assertion here is
# explainability: every TypologyMatch's Evidence must cite the real
# transaction ids that triggered it -- never an unexplained score.
from __future__ import annotations

from datetime import datetime, timedelta

from aml.monitor import check_anomaly, check_layering, check_structuring, sweep
from aml.scoring import match_typologies, score_case
from aml.state import Case, Transaction


def _txn(txn_id, account_id, counterparty, amount, ts, memo=""):
    return Transaction(
        txn_id=txn_id, account_id=account_id,
        counterparty=counterparty, amount=amount, ts=ts, memo=memo)


BASE = datetime(2026, 1, 1)


# -- structuring: several sub-threshold deposits, tight window ---------

def test_check_structuring_fires_on_sub_threshold_deposits():
    txns = [
        _txn("txn_1", "acct-1", "cp-1", 9_500.0, BASE),
        _txn("txn_2", "acct-1", "cp-1", 9_400.0, BASE + timedelta(days=1)),
        _txn("txn_3", "acct-1", "cp-1", 9_600.0, BASE + timedelta(days=2)),
    ]
    alerts = check_structuring(txns)
    assert len(alerts) == 1
    assert alerts[0].rule == "structuring"
    assert set(alerts[0].txn_ids) == {"txn_1", "txn_2", "txn_3"}


def test_check_structuring_does_not_fire_below_min_count():
    txns = [
        _txn("txn_1", "acct-1", "cp-1", 9_500.0, BASE),
        _txn("txn_2", "acct-1", "cp-1", 9_400.0, BASE + timedelta(days=1)),
    ]
    assert check_structuring(txns) == []


def test_check_structuring_ignores_amounts_at_or_above_threshold():
    txns = [
        _txn("txn_1", "acct-1", "cp-1", 10_000.0, BASE),
        _txn("txn_2", "acct-1", "cp-1", 10_500.0, BASE + timedelta(days=1)),
        _txn("txn_3", "acct-1", "cp-1", 11_000.0, BASE + timedelta(days=2)),
    ]
    assert check_structuring(txns) == []


def test_check_structuring_ignores_amounts_well_under_margin():
    txns = [
        _txn("txn_1", "acct-1", "cp-1", 100.0, BASE),
        _txn("txn_2", "acct-1", "cp-1", 200.0, BASE + timedelta(days=1)),
        _txn("txn_3", "acct-1", "cp-1", 300.0, BASE + timedelta(days=2)),
    ]
    assert check_structuring(txns) == []


# -- layering: funds arrive, then fan out within a short dwell ---------

def test_check_layering_fires_on_fast_fan_out():
    txns = [
        _txn("txn_in", "acct-1", "cp-in", 40_000.0, BASE)] + [
        _txn(f"txn_out_{i}", "acct-1", f"cp-{i}", -1_000.0,
             BASE + timedelta(minutes=10 * i))
        for i in range(4)
    ]
    alerts = check_layering(txns)
    assert len(alerts) == 1
    assert alerts[0].rule == "layering"
    assert "txn_in" in alerts[0].txn_ids


def test_check_layering_does_not_fire_below_min_hops():
    txns = [
        _txn("txn_in", "acct-1", "cp-in", 40_000.0, BASE)] + [
        _txn(f"txn_out_{i}", "acct-1", f"cp-{i}", -1_000.0,
             BASE + timedelta(minutes=10 * i))
        for i in range(3)
    ]
    assert check_layering(txns) == []


def test_check_layering_does_not_fire_outside_window():
    txns = [
        _txn("txn_in", "acct-1", "cp-in", 40_000.0, BASE)] + [
        _txn(f"txn_out_{i}", "acct-1", f"cp-{i}", -1_000.0,
             BASE + timedelta(hours=3, minutes=10 * i))
        for i in range(4)
    ]
    assert check_layering(txns) == []


# -- anomaly: z-score against the account's own history ----------------

def test_check_anomaly_fires_on_far_outlier():
    history = {"acct-1": [100.0, 110.0, 95.0, 105.0, 100.0]}
    txns = [_txn("txn_1", "acct-1", "cp-1", 5_000.0, BASE)]
    alerts = check_anomaly(txns, history)
    assert len(alerts) == 1
    assert alerts[0].rule == "anomaly"
    assert alerts[0].txn_ids == ["txn_1"]


def test_check_anomaly_ignores_amounts_within_normal_range():
    history = {"acct-1": [100.0, 110.0, 95.0, 105.0, 100.0]}
    txns = [_txn("txn_1", "acct-1", "cp-1", 102.0, BASE)]
    assert check_anomaly(txns, history) == []


def test_check_anomaly_ignores_accounts_with_thin_history():
    history = {"acct-1": [100.0, 110.0]}  # fewer than 5 points
    txns = [_txn("txn_1", "acct-1", "cp-1", 999_999.0, BASE)]
    assert check_anomaly(txns, history) == []


def test_sweep_runs_every_rule_in_order():
    structuring_txns = [
        _txn("txn_1", "acct-1", "cp-1", 9_500.0, BASE),
        _txn("txn_2", "acct-1", "cp-1", 9_400.0, BASE + timedelta(days=1)),
        _txn("txn_3", "acct-1", "cp-1", 9_600.0, BASE + timedelta(days=2)),
    ]
    alerts = sweep(structuring_txns, history={})
    assert [a.rule for a in alerts] == ["structuring"]


# -- match_typologies / score_case: explainability of the risk score --

def test_match_typologies_carries_evidence_with_real_txn_ids():
    txns = [
        _txn("txn_1", "acct-1", "cp-1", 9_500.0, BASE),
        _txn("txn_2", "acct-1", "cp-1", 9_400.0, BASE + timedelta(days=1)),
        _txn("txn_3", "acct-1", "cp-1", 9_600.0, BASE + timedelta(days=2)),
    ]
    alerts = check_structuring(txns)
    matches = match_typologies(alerts)
    assert len(matches) == 1
    match = matches[0]
    assert match.name == "structuring"
    assert 0.0 < match.confidence <= 0.95
    # explainability: every match's evidence cites real txn ids
    assert len(match.evidence) > 0
    for ev in match.evidence:
        assert ev.txn_ids  # never empty
        assert set(ev.txn_ids) <= {"txn_1", "txn_2", "txn_3"}


def test_match_typologies_returns_empty_for_no_alerts():
    assert match_typologies([]) == []


def test_score_case_is_zero_with_no_typologies():
    case = Case(case_id="case_1", subject_account="acct-1")
    assert score_case(case) == 0.0


def test_score_case_is_positive_and_bounded_with_typologies():
    txns = [
        _txn("txn_1", "acct-1", "cp-1", 9_500.0, BASE),
        _txn("txn_2", "acct-1", "cp-1", 9_400.0, BASE + timedelta(days=1)),
        _txn("txn_3", "acct-1", "cp-1", 9_600.0, BASE + timedelta(days=2)),
    ]
    case = Case(case_id="case_1", subject_account="acct-1")
    case.typologies = match_typologies(check_structuring(txns))
    score = score_case(case)
    assert 0.0 < score <= 100.0
    # score_case logs its own derivation onto the case's audit trail
    assert any("risk_score=" in entry for entry in case.audit_log)
