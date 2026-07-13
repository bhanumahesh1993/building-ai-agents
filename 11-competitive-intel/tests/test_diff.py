# tests/test_diff.py — semantic-diff drift gate, no live model/DB needed
from __future__ import annotations

import os

import pytest

from monitor.nodes.diff import DRIFT_THRESHOLD, _cosine_distance


def test_identical_vectors_have_zero_distance():
    v = [1.0, 2.0, 3.0]
    assert _cosine_distance(v, v) == pytest.approx(0.0, abs=1e-9)


def test_opposite_vectors_have_max_distance():
    v = [1.0, 0.0]
    assert _cosine_distance(v, [-1.0, 0.0]) == pytest.approx(2.0)


def test_orthogonal_vectors_are_distance_one():
    assert _cosine_distance(
        [1.0, 0.0], [0.0, 1.0]) == pytest.approx(1.0)


def test_small_perturbation_stays_under_drift_threshold():
    # A near-identical embedding (e.g. rephrasing, typo
    # fix) should not trip the drift gate.
    base = [1.0, 0.0, 0.0]
    nudged = [0.999, 0.02, 0.0]
    assert _cosine_distance(base, nudged) < DRIFT_THRESHOLD


def test_large_shift_exceeds_drift_threshold():
    base = [1.0, 0.0, 0.0]
    shifted = [0.0, 1.0, 0.0]
    assert _cosine_distance(base, shifted) > DRIFT_THRESHOLD


def test_distance_is_symmetric():
    a, b = [1.0, 2.0, 0.5], [0.3, -1.0, 2.0]
    assert _cosine_distance(a, b) == pytest.approx(
        _cosine_distance(b, a))


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a live ANTHROPIC_API_KEY for the confirmation call",
)
def test_diff_node_calls_live_model():
    from monitor.nodes.diff import diff_node

    state = {"_worker_result": {
        "url": "https://acme.example.com/pricing",
        "competitor": "Acme Corp",
        "kind": "pricing",
        "text": "New: $49/mo plan added.",
        "embedding": [1.0, 0.0, 0.0],
        "previous": {
            "text": "Plans start at $29/mo.",
            "embedding": [0.0, 1.0, 0.0],
        },
    }}
    result = diff_node(state)
    assert "changes" in result
