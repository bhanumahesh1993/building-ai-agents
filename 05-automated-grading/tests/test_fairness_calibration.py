# tests/test_fairness_calibration.py
from __future__ import annotations

import evals.calibrate as calibrate_mod
import evals.fairness as fairness_mod

SCORES_A = [
    {"criterion": "Thesis & Argument", "points": 4, "max_points": 4,
     "evidence": "q"},
    {"criterion": "Use of Evidence", "points": 4, "max_points": 4,
     "evidence": "q"},
    {"criterion": "Writing Mechanics", "points": 1, "max_points": 4,
     "evidence": "q"},
]

SCORES_B = [
    {"criterion": "Thesis & Argument", "points": 4, "max_points": 4,
     "evidence": "q"},
    {"criterion": "Use of Evidence", "points": 4, "max_points": 4,
     "evidence": "q"},
    {"criterion": "Writing Mechanics", "points": 4, "max_points": 4,
     "evidence": "q"},
]


def test_content_subscore_excludes_writing_mechanics():
    """Fairness: a register/polish criterion must not leak into
    the content comparison used to catch register bias."""
    result = {"scores": SCORES_A}
    assert fairness_mod.content_subscore(result) == 8


def test_fairness_gap_is_zero_for_matching_content_scores(monkeypatch):
    """Two essays with the same argument but different writing
    polish should show a fairness gap of 0 once mechanics are
    excluded -- deterministic given a stubbed scorer."""
    calls = iter([{"scores": SCORES_A}, {"scores": SCORES_B}])
    monkeypatch.setattr(
        fairness_mod, "_score_one",
        lambda prompt, essay: next(calls))

    pairs = [(
        {"id": "a1", "prompt": "p", "essay": "polished essay"},
        {"id": "b1", "prompt": "p", "essay": "rough essay"},
    )]
    gaps = fairness_mod.fairness_gap(pairs)
    assert gaps == [{"pair": ("a1", "b1"), "gap": 0}]


def test_calibrate_reports_agreement_against_golden_labels(monkeypatch):
    """Calibration: model totals within TOLERANCE of the teacher's
    total should count as agreement -- verified deterministically
    against a stubbed grader, no live model or golden.json needed."""
    rows = [
        {"prompt": "p", "essay": "e1", "teacher_total": 13},
        {"prompt": "p", "essay": "e2", "teacher_total": 20},
    ]
    monkeypatch.setattr(
        calibrate_mod, "_load", lambda path: rows)
    monkeypatch.setattr(
        calibrate_mod, "_score_one",
        lambda prompt, essay: {"scores": SCORES_A}
        if essay == "e1" else {"scores": SCORES_B})

    report = calibrate_mod.calibrate("unused.json")
    assert report["n"] == 2
    # e1: model total 9 vs teacher 13 -> diff 4 (outside tolerance)
    # e2: model total 12 vs teacher 20 -> diff 8 (outside tolerance)
    assert report["mean_abs_error"] == 6.0
    assert report["agreement_rate"] == 0.0


def test_calibrate_agrees_when_within_tolerance(monkeypatch):
    rows = [{"prompt": "p", "essay": "e1", "teacher_total": 9}]
    monkeypatch.setattr(calibrate_mod, "_load", lambda path: rows)
    monkeypatch.setattr(
        calibrate_mod, "_score_one",
        lambda prompt, essay: {"scores": SCORES_A})

    report = calibrate_mod.calibrate("unused.json")
    assert report["mean_abs_error"] == 0.0
    assert report["agreement_rate"] == 1.0
