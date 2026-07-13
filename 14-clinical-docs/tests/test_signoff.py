# tests/test_signoff.py
"""Mandatory clinician sign-off gate.

No code path may hand back a "final" note -- via the sign-off
endpoint or the visit-fetch endpoint -- unless every flagged claim
was either edited out or explicitly resolved by a named clinician
with a real attestation. These tests exercise the FastAPI route
functions directly (no HTTP layer, no model calls) so they stay
deterministic and fast.
"""
from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

import scribe.app as app_module
from scribe.app import SignOffRequest, get_visit, sign_off
from scribe.models import ClinicalClaim, Provenance, SOAPNote, TraceabilityFlag

ATTESTATION = "I attest this note is accurate and complete."


@pytest.fixture(autouse=True)
def _isolated_visits():
    """Give every test a clean in-memory visit store."""
    app_module.VISITS.clear()
    yield
    app_module.VISITS.clear()


def _note_with_claim(text: str) -> SOAPNote:
    prov = Provenance(quote="q", speaker="patient", turn_index=0)
    claim = ClinicalClaim(text=text, provenance=prov)
    return SOAPNote(subjective=[claim], assessment=[claim], plan=[claim])


def _seed_visit(visit_id: str, note: SOAPNote, flags=None) -> None:
    app_module.VISITS[visit_id] = {
        "status": "pending_signoff",
        "transcript": "irrelevant for this gate",
        "note": note,
        "flags": flags or [],
        "score": 1.0,
    }


def test_get_visit_404_for_unknown_visit():
    with pytest.raises(HTTPException) as exc:
        get_visit("does-not-exist")
    assert exc.value.status_code == 404


def test_get_visit_blocks_unsigned_draft():
    """A draft is never returned as final, no matter what."""
    visit_id = "v-unsigned"
    _seed_visit(visit_id, _note_with_claim("knee pain"))
    with pytest.raises(HTTPException) as exc:
        get_visit(visit_id)
    assert exc.value.status_code == 409


def test_signoff_rejects_short_attestation():
    visit_id = "v-short-attest"
    note = _note_with_claim("knee pain")
    _seed_visit(visit_id, note)
    req = SignOffRequest(
        clinician_name="Dr. Lee", credential="MD",
        edited_note=note, resolved_flags=[], attestation="ok")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(sign_off(visit_id, req))
    assert exc.value.status_code == 400
    assert app_module.VISITS[visit_id]["status"] == "pending_signoff"


def test_signoff_rejects_unresolved_flags():
    """No code path finalizes a note while a flagged claim
    survives -- neither edited out nor explicitly resolved."""
    visit_id = "v-unresolved"
    flag = TraceabilityFlag(
        section="assessment", claim_text="likely fracture",
        reason="no provenance attached")
    note = _note_with_claim("likely fracture")
    _seed_visit(visit_id, note, flags=[flag])
    req = SignOffRequest(
        clinician_name="Dr. Lee", credential="MD",
        edited_note=note, resolved_flags=[], attestation=ATTESTATION)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(sign_off(visit_id, req))
    assert exc.value.status_code == 400
    assert app_module.VISITS[visit_id]["status"] == "pending_signoff"


def test_signoff_succeeds_when_flag_is_edited_out():
    visit_id = "v-edited-out"
    flag = TraceabilityFlag(
        section="assessment", claim_text="likely fracture",
        reason="no provenance attached")
    _seed_visit(visit_id, _note_with_claim("likely fracture"), flags=[flag])
    edited = _note_with_claim("mild strain, no fracture noted")
    req = SignOffRequest(
        clinician_name="Dr. Lee", credential="MD",
        edited_note=edited, resolved_flags=[], attestation=ATTESTATION)
    result = asyncio.run(sign_off(visit_id, req))
    assert result["status"] == "signed"
    assert app_module.VISITS[visit_id]["status"] == "signed"


def test_signoff_succeeds_when_flag_explicitly_resolved():
    visit_id = "v-explicit-resolve"
    flag = TraceabilityFlag(
        section="assessment", claim_text="likely fracture",
        reason="no provenance attached")
    note = _note_with_claim("likely fracture")
    _seed_visit(visit_id, note, flags=[flag])
    req = SignOffRequest(
        clinician_name="Dr. Lee", credential="MD",
        edited_note=note, resolved_flags=["likely fracture"],
        attestation=ATTESTATION)
    result = asyncio.run(sign_off(visit_id, req))
    assert result["status"] == "signed"


def test_get_visit_returns_note_only_after_signoff():
    visit_id = "v-final"
    note = _note_with_claim("knee pain")
    _seed_visit(visit_id, note)
    req = SignOffRequest(
        clinician_name="Dr. Lee", credential="MD",
        edited_note=note, resolved_flags=[], attestation=ATTESTATION)
    asyncio.run(sign_off(visit_id, req))
    result = get_visit(visit_id)
    assert result["note"] == note


def test_signoff_404_when_no_draft_pending():
    req = SignOffRequest(
        clinician_name="Dr. Lee", credential="MD",
        edited_note=_note_with_claim("x"), resolved_flags=[],
        attestation=ATTESTATION)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(sign_off("no-such-visit", req))
    assert exc.value.status_code == 404


def test_signoff_is_idempotent_gate_not_reopenable():
    """Once signed, status is 'signed' -- a repeat sign-off
    attempt finds no visit left in 'pending_signoff'."""
    visit_id = "v-double-signoff"
    note = _note_with_claim("knee pain")
    _seed_visit(visit_id, note)
    req = SignOffRequest(
        clinician_name="Dr. Lee", credential="MD",
        edited_note=note, resolved_flags=[], attestation=ATTESTATION)
    asyncio.run(sign_off(visit_id, req))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(sign_off(visit_id, req))
    assert exc.value.status_code == 404
