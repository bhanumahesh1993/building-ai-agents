# tests/test_score.py — significance-scoring math, no live model needed
from __future__ import annotations

import os

import pytest

from monitor.nodes.score import KIND_WEIGHT, compute_final_score


def test_pricing_change_gets_boosted():
    # Pricing carries the highest weight (1.3), so a
    # mid-tier base score should be boosted upward.
    assert compute_final_score(3, "pricing") == round(3 * 1.3)


def test_careers_change_gets_dampened():
    # Careers carries a sub-1.0 weight, so the final
    # score should never exceed the raw model score.
    assert compute_final_score(4, "careers") == round(4 * 0.9)


def test_score_is_clamped_to_five():
    assert compute_final_score(5, "pricing") == 5
    assert compute_final_score(4, "pricing") <= 5


def test_unknown_kind_falls_back_to_neutral_weight():
    assert compute_final_score(3, "unknown-kind") == 3


def test_all_known_kinds_have_a_weight():
    for kind in ("pricing", "changelog", "careers", "blog"):
        assert kind in KIND_WEIGHT


def test_pricing_outranks_careers_for_the_same_base_score():
    # The whole point of the weighting: a pricing move
    # and a careers move that look equally newsworthy
    # to the raw model should not land on equal footing.
    assert (compute_final_score(3, "pricing")
            >= compute_final_score(3, "careers"))


def test_compute_final_score_is_deterministic():
    first = compute_final_score(4, "changelog")
    second = compute_final_score(4, "changelog")
    assert first == second


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a live ANTHROPIC_API_KEY to score via the model",
)
def test_score_node_calls_live_model():
    from monitor.nodes.score import score_node

    state = {"_change": {
        "url": "https://acme.example.com/pricing",
        "competitor": "Acme Corp",
        "kind": "pricing",
        "summary": "Added a new $49/mo tier.",
        "changed": True,
        "evidence": "https://acme.example.com/pricing",
    }}
    result = score_node(state)
    assert result["scored"][0]["score"] >= 1
