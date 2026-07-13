# tests/test_consolidate.py
from __future__ import annotations

from review.nodes.consolidate import consolidate_node


def _vf(path, line, severity, claim, verdict="confirmed",
        reviewer="correctness"):
    return {
        "finding": {
            "reviewer": reviewer, "path": path, "line": line,
            "severity": severity, "claim": claim, "evidence": "x",
        },
        "verdict": verdict,
        "rationale": "fake rationale",
    }


def test_confirmed_findings_are_sorted_by_severity_calibration():
    # Deliberately scrambled input order.
    verified = [
        _vf("a.py", 1, "low", "style nit"),
        _vf("b.py", 2, "critical", "sql injection"),
        _vf("c.py", 3, "medium", "no tests"),
        _vf("d.py", 4, "high", "off by one"),
    ]
    out = consolidate_node({"verified": verified, "truncated": False})
    report = out["report"]
    idx_critical = report.index("sql injection")
    idx_high = report.index("off by one")
    idx_medium = report.index("no tests")
    idx_low = report.index("style nit")
    assert idx_critical < idx_high < idx_medium < idx_low


def test_refuted_findings_are_excluded_from_the_report_body():
    verified = [
        _vf("a.py", 1, "critical", "real bug", verdict="confirmed"),
        _vf("a.py", 2, "critical", "hallucinated bug", verdict="refuted"),
    ]
    out = consolidate_node({"verified": verified, "truncated": False})
    assert "Confirmed: 1" in out["report"]
    assert "Refuted by verification: 1" in out["report"]
    assert "hallucinated bug" not in out["report"]
    assert "real bug" in out["report"]


def test_duplicate_findings_from_multiple_reviewers_are_deduped():
    verified = [
        _vf("a.py", 10, "high", "same underlying bug reported twice",
            reviewer="correctness"),
        _vf("a.py", 10, "high", "same underlying bug reported twice",
            reviewer="security"),
    ]
    out = consolidate_node({"verified": verified, "truncated": False})
    assert out["report"].count(
        "same underlying bug reported twice") == 1
    assert "Confirmed: 1" in out["report"]


def test_truncated_note_appears_when_diff_was_capped():
    out = consolidate_node({"verified": [], "truncated": True})
    assert "capped" in out["report"]


def test_no_truncated_note_when_diff_was_not_capped():
    out = consolidate_node({"verified": [], "truncated": False})
    assert "capped" not in out["report"]
