# tests/test_live_api.py
from __future__ import annotations

import os

import pytest

from grading.nodes.score import _score_one

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set -- skipping live-model call",
)


def test_score_one_against_the_real_model():
    """Smoke test the actual grading model end-to-end. Only runs
    when ANTHROPIC_API_KEY is present (e.g. in CI secrets or a
    developer's local .env) -- never part of the offline suite."""
    essay = (
        "The Emancipation Proclamation, issued in 1863, declared "
        "that enslaved people in Confederate territory were free. "
        "This shifted the Civil War's purpose toward abolition."
    )
    result = _score_one(
        prompt="Explain the significance of the "
               "Emancipation Proclamation.",
        essay=essay,
    )
    assert "scores" in result
    assert len(result["scores"]) == 5
    for s in result["scores"]:
        assert 0 <= s["points"] <= s["max_points"]
