# tests/test_citations.py — mechanical citation self-check
from __future__ import annotations

import os

import pytest

from assistant.citations import check, find_out_of_range_citations


def test_finds_no_gaps_when_all_citations_in_range():
    answer = "Water boils at 100C [1] at sea level [2]."
    assert find_out_of_range_citations(answer, n_sources=2) == []


def test_flags_citation_beyond_source_count():
    answer = "This claim cites a source that does not exist [5]."
    assert find_out_of_range_citations(answer, n_sources=2) == [5]


def test_flags_zero_and_negative_style_citations():
    # [0] is out of the 1-indexed source range.
    answer = "Bad reference here [0]."
    assert find_out_of_range_citations(answer, n_sources=3) == [0]


def test_dedupes_and_sorts_out_of_range_hits():
    answer = "Two bad refs [9] and [7] and a repeat [9]."
    assert find_out_of_range_citations(answer, n_sources=2) == [7, 9]


def test_no_citations_is_not_out_of_range():
    answer = "A plain sentence with no brackets at all."
    assert find_out_of_range_citations(answer, n_sources=3) == []


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a live ANTHROPIC_API_KEY for the LLM gap check",
)
def test_check_calls_live_model():
    result = check("An answer with [1] and [9].", n_sources=1)
    assert result["out_of_range_cites"] == [9]
    assert result["grounded"] is False
