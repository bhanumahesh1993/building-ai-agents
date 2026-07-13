# tests/test_rubric.py
from __future__ import annotations

from grading.rubric import RUBRIC, TOTAL_POINTS, rubric_block


def test_total_points_matches_sum_of_criteria():
    assert TOTAL_POINTS == sum(c["max_points"] for c in RUBRIC)


def test_rubric_has_five_criteria():
    assert len(RUBRIC) == 5
    names = {c["name"] for c in RUBRIC}
    assert "Writing Mechanics" in names
    assert "Historical Accuracy" in names


def test_rubric_block_renders_every_criterion():
    block = rubric_block(RUBRIC)
    for c in RUBRIC:
        assert c["name"] in block
        assert f"(0-{c['max_points']})" in block
