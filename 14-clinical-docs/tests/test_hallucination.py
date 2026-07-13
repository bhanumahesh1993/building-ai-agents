# tests/test_hallucination.py
"""Structure of the hallucination-rate check result. The judge
itself is an LLM call (see tests/test_live_api.py for the live,
skipif-gated exercise of it); this module only pins down the
typed contract every caller of evals.judge relies on."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from evals.judge import HallucinationCheck


def test_hallucination_check_structure():
    check = HallucinationCheck(
        unsupported_count=2,
        unsupported_examples=["claim a", "claim b"])
    assert check.unsupported_count == 2
    assert check.unsupported_examples == ["claim a", "claim b"]


def test_hallucination_check_allows_zero_with_no_examples():
    check = HallucinationCheck(
        unsupported_count=0, unsupported_examples=[])
    assert check.unsupported_count == 0
    assert check.unsupported_examples == []


def test_hallucination_check_requires_count_field():
    with pytest.raises(ValidationError):
        HallucinationCheck(unsupported_examples=["x"])
