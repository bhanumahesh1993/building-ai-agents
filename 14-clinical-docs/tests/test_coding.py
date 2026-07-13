# tests/test_coding.py
"""ICD-suggestion structure: the code shape, and the code-level
guarantee that suggest_codes() never reaches the model when
there is nothing verified left to code from."""
from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from scribe.coding import suggest_codes
from scribe.models import (
    ClinicalClaim, ICDCode, ICDSuggestions, SOAPNote, TraceabilityFlag,
)


def test_icd_code_accepts_valid_formats():
    ICDCode(
        code="M25.561", description="Pain in right knee",
        supporting_text="knee pain", confidence="high")
    ICDCode(
        code="E11.9", description="Type 2 diabetes without complications",
        supporting_text="diabetes", confidence="medium")


@pytest.mark.parametrize("bad_code", [
    "m25.561",     # lowercase leading letter
    "25.561",      # missing leading letter
    "M25.56100",   # too many digits after the dot
    "M-25",        # bad separator
    "",            # empty
])
def test_icd_code_rejects_malformed_codes(bad_code):
    with pytest.raises(ValidationError):
        ICDCode(
            code=bad_code, description="x",
            supporting_text="x", confidence="low")


def test_icd_suggestions_wraps_a_code_list():
    codes = [ICDCode(
        code="M25.561", description="d",
        supporting_text="t", confidence="high")]
    assert ICDSuggestions(codes=codes).codes == codes


def test_icd_suggestions_allows_empty_list():
    assert ICDSuggestions(codes=[]).codes == []


def test_suggest_codes_short_circuits_without_calling_model():
    """When every assessment line is already flagged, there's
    nothing verified left to code -- suggest_codes must return
    [] without ever reaching the network/model."""
    claim = ClinicalClaim(text="likely fracture")
    note = SOAPNote(
        subjective=[claim], assessment=[claim], plan=[claim])
    flag = TraceabilityFlag(
        section="assessment", claim_text="likely fracture",
        reason="no provenance attached")
    codes = asyncio.run(suggest_codes(note, [flag]))
    assert codes == []
