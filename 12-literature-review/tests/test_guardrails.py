# tests/test_guardrails.py — deterministic guardrail logic
# (citation allow-listing feeds contradiction/hypothesis grounding).
from __future__ import annotations

from lit_review.tools import check_hedging, validate_citations


def test_validate_citations_all_known():
    text = "Findings from [2501.01234] and [2502.05678] agree."
    known = {"2501.01234", "2502.05678"}
    result = validate_citations(text, known)
    assert result["clean"] is True
    assert result["hallucinated"] == []
    assert result["cited"] == ["2501.01234", "2502.05678"]


def test_validate_citations_flags_hallucination():
    text = "This claim cites a paper not in the corpus [9999.99999]."
    known = {"2501.01234"}
    result = validate_citations(text, known)
    assert result["clean"] is False
    assert result["hallucinated"] == ["9999.99999"]


def test_validate_citations_dedupes_and_sorts():
    text = "[2502.00002] then again [2501.00001] and [2502.00002]."
    known = {"2501.00001", "2502.00002"}
    result = validate_citations(text, known)
    assert result["cited"] == ["2501.00001", "2502.00002"]


def test_validate_citations_no_brackets_is_clean():
    result = validate_citations("A plain sentence with no citations.", set())
    assert result["cited"] == []
    assert result["clean"] is True


def test_check_hedging_flags_clean_hedge():
    text = ("This finding may warrant further investigation, and "
            "appears consistent with prior work.")
    result = check_hedging(text)
    assert result["hedged"] is True
    assert result["overclaim_terms"] == []
    assert result["ok"] is True


def test_check_hedging_flags_overclaim():
    text = "This finding definitively proves the hypothesis."
    result = check_hedging(text)
    assert result["overclaim_terms"] != []
    assert result["ok"] is False


def test_check_hedging_unhedged_text_is_not_ok():
    text = "The sky is blue."
    result = check_hedging(text)
    assert result["hedged"] is False
    assert result["ok"] is False


def test_check_hedging_hedge_and_overclaim_together_is_not_ok():
    text = "This may be true, but it definitively proves everything."
    result = check_hedging(text)
    assert result["hedged"] is True
    assert result["overclaim_terms"] != []
    assert result["ok"] is False
