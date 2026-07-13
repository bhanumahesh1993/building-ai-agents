# tests/test_gate.py
from __future__ import annotations

import pytest

from review.github_stub import last_check
from review.nodes.gate import gate_node

KNOWN_DECISIONS = {"block", "approve_with_comments"}


def _vf(severity, verdict="confirmed", claim="issue"):
    return {
        "finding": {
            "reviewer": "security", "path": "a.py", "line": 1,
            "severity": severity, "claim": claim, "evidence": "x",
        },
        "verdict": verdict,
        "rationale": "fake rationale",
    }


def test_blocking_severity_blocks_and_posts_failure_check():
    state = {"pr_id": "gate-block-1",
              "verified": [_vf("critical")], "report": "r"}
    out = gate_node(state)
    assert out["decision"] == "block"
    check = last_check("gate-block-1")
    assert check is not None
    assert check.conclusion == "failure"


def test_non_blocking_confirmed_findings_never_auto_merge():
    state = {"pr_id": "gate-nonblock-1",
              "verified": [_vf("low")], "report": "r"}
    out = gate_node(state)
    assert out["decision"] == "approve_with_comments"
    assert out["decision"] not in ("merge", "auto_merge", "merged")
    check = last_check("gate-nonblock-1")
    assert check.conclusion == "neutral"


def test_no_findings_at_all_still_posts_a_check_never_silently_merges():
    state = {"pr_id": "gate-empty-1", "verified": [], "report": "no issues"}
    out = gate_node(state)
    assert out["decision"] == "approve_with_comments"
    # The structural gate always posts a check -- there is no code
    # path that merges without one.
    assert last_check("gate-empty-1") is not None


def test_refuted_critical_finding_does_not_block():
    # A critical claim that adversarial verification refuted must
    # not gate the merge -- only *confirmed* findings count.
    state = {"pr_id": "gate-refuted-1",
              "verified": [_vf("critical", verdict="refuted")],
              "report": "r"}
    out = gate_node(state)
    assert out["decision"] == "approve_with_comments"


@pytest.mark.parametrize("severity", ["critical", "high", "medium", "low"])
def test_decision_is_always_one_of_two_known_values(severity):
    state = {"pr_id": f"gate-param-{severity}",
              "verified": [_vf(severity)], "report": "r"}
    out = gate_node(state)
    assert out["decision"] in KNOWN_DECISIONS


def test_multiple_confirmed_findings_mixed_severity_still_blocks_once():
    state = {
        "pr_id": "gate-mixed-1",
        "verified": [_vf("low"), _vf("high"), _vf("medium")],
        "report": "r",
    }
    out = gate_node(state)
    assert out["decision"] == "block"
