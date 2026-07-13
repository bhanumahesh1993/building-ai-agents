# tests/test_live_api.py
"""End-to-end pipeline through the real Pydantic AI agents.

Skipped unless ANTHROPIC_API_KEY is set, so the offline suite
(uv run --no-project pytest -q) stays deterministic and keyless.
"""
from __future__ import annotations

import asyncio
import os

import pytest

from evals.judge import hallucination_rate
from scribe.coding import suggest_codes
from scribe.extract import extract_note
from scribe.verify import verify_note

requires_live_api = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires ANTHROPIC_API_KEY for a live model call",
)

TRANSCRIPT = (
    "Dr: What brings you in today?\n"
    "Pt: I've had a sore throat and mild fever for two days.\n"
    "Dr: Any cough or trouble swallowing?\n"
    "Pt: No cough, but swallowing hurts a bit.\n"
    "Dr: Your throat looks red, no white patches, no swelling.\n"
    "Dr: This looks like a viral pharyngitis. Rest, fluids, "
    "and ibuprofen for the pain."
)

SECTIONS = ("subjective", "objective", "assessment", "plan")


@requires_live_api
def test_extract_note_live():
    note = asyncio.run(extract_note(TRANSCRIPT))
    assert note.subjective
    assert note.assessment
    assert note.plan


@requires_live_api
def test_verify_note_live_scores_traceability():
    note = asyncio.run(extract_note(TRANSCRIPT))
    report = asyncio.run(verify_note(note, TRANSCRIPT))
    assert 0.0 <= report.traceability_score <= 1.0


@requires_live_api
def test_suggest_codes_live_returns_structured_codes():
    note = asyncio.run(extract_note(TRANSCRIPT))
    report = asyncio.run(verify_note(note, TRANSCRIPT))
    codes = asyncio.run(suggest_codes(note, report.flags))
    assert isinstance(codes, list)
    for code in codes:
        assert code.confidence in ("high", "medium", "low")


@requires_live_api
def test_hallucination_rate_live_checks_final_claims():
    note = asyncio.run(extract_note(TRANSCRIPT))
    report = asyncio.run(verify_note(note, TRANSCRIPT))
    flagged = {f.claim_text for f in report.flags}
    kept = [
        c.text for section in SECTIONS
        for c in getattr(note, section)
        if c.text not in flagged
    ]
    check = asyncio.run(hallucination_rate(TRANSCRIPT, kept))
    assert check.unsupported_count >= 0
