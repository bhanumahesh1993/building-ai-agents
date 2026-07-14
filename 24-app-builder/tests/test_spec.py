# tests/test_spec.py
from __future__ import annotations

import pytest

from builder.spec import (
    AcceptanceCriterion, AppSpec, EarsPattern, MAX_CRITERIA,
    render_criterion,
)


def _crit(pattern: EarsPattern, **kw) -> AcceptanceCriterion:
    return AcceptanceCriterion(
        id="AC-1", pattern=pattern, response="do the thing",
        **kw)


def test_ubiquitous_pattern_has_no_trigger_clause():
    c = _crit(EarsPattern.UBIQUITOUS)
    assert render_criterion(c) == "The system shall do the thing."


def test_event_pattern_renders_when_clause():
    c = _crit(EarsPattern.EVENT, trigger="a vote is cast")
    assert render_criterion(c) == (
        "When a vote is cast, the system shall do the thing.")


def test_state_pattern_renders_while_clause():
    c = _crit(EarsPattern.STATE, trigger="the poll is open")
    assert render_criterion(c) == (
        "While the poll is open, the system shall do the thing.")


def test_unwanted_pattern_renders_if_then_clause():
    c = _crit(EarsPattern.UNWANTED, trigger="the poll is closed")
    assert render_criterion(c) == (
        "If the poll is closed, then the system shall "
        "do the thing.")


def test_optional_pattern_renders_where_clause():
    c = _crit(EarsPattern.OPTIONAL, trigger="anonymity is on")
    assert render_criterion(c) == (
        "Where anonymity is on, the system shall do the thing.")


def _spec_with(n: int) -> AppSpec:
    return AppSpec(
        name="t", goal="g",
        acceptance_criteria=[
            AcceptanceCriterion(
                id=f"AC-{i}", pattern=EarsPattern.UBIQUITOUS,
                response="r")
            for i in range(n)
        ])


def test_check_scope_allows_criteria_at_the_cap():
    _spec_with(MAX_CRITERIA).check_scope()  # must not raise


def test_check_scope_refuses_gold_plated_specs():
    """More than MAX_CRITERIA criteria is a scope violation,
    not something the builder should silently accept."""
    with pytest.raises(ValueError):
        _spec_with(MAX_CRITERIA + 1).check_scope()
