# tests/test_routing.py
from __future__ import annotations

import pytest

from support.graph import route_after_answer, route_after_classify


@pytest.mark.parametrize("category", ["feature_request", "abuse"])
def test_off_kb_categories_always_escalate(category):
    state = {"category": category, "confidence": 1.0}
    assert route_after_classify(state) == "escalate"


def test_low_confidence_escalates_even_in_kb_category():
    state = {"category": "billing", "confidence": 0.2}
    assert route_after_classify(state) == "escalate"


def test_confident_kb_category_goes_to_retrieve():
    state = {"category": "how_to", "confidence": 0.9}
    assert route_after_classify(state) == "retrieve"


def test_confidence_boundary_is_exclusive():
    # Exactly 0.5 should NOT escalate — only strictly < 0.5 does.
    state = {"category": "billing", "confidence": 0.5}
    assert route_after_classify(state) == "retrieve"


def test_grounded_answer_resolves():
    assert route_after_answer({"grounded": True}) == "resolve"


def test_ungrounded_answer_escalates():
    assert route_after_answer({"grounded": False}) == "escalate"


def test_missing_grounded_key_escalates():
    # answer_node always sets "grounded", but the router must
    # never silently resolve a ticket if it's absent — never
    # let a guess ship.
    assert route_after_answer({}) == "escalate"
