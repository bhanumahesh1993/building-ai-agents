# scribe/app.py
from __future__ import annotations

import re
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .coding import suggest_codes
from .extract import extract_note
from .models import SOAPNote
from .verify import verify_note

app = FastAPI(title="Ambient Documentation Assistant")

# In-memory store for a teaching build -- swap for a
# real database before this touches anything real.
VISITS: dict[str, dict] = {}

_PHI_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),   # SSN-shaped
    re.compile(r"\b\d{10}\b"),               # MRN-shaped
]


def redact_for_trace(text: str) -> str:
    """Strip identifier-shaped text before it reaches
    any external trace, log, or observability backend."""
    out = text
    for pat in _PHI_PATTERNS:
        out = pat.sub("[redacted]", out)
    return out


class DraftRequest(BaseModel):
    transcript: str


class SignOffRequest(BaseModel):
    clinician_name: str
    credential: Literal["MD", "DO", "NP", "PA"]
    edited_note: SOAPNote
    resolved_flags: list[str] = []
    attestation: str


def _claim_texts(note: SOAPNote) -> list[str]:
    sections = (
        "subjective", "objective", "assessment", "plan")
    return [
        c.text for s in sections
        for c in getattr(note, s)]


@app.post("/visits/{visit_id}/draft")
async def create_draft(visit_id: str, req: DraftRequest):
    """Run extract -> verify -> code. Never final."""
    note = await extract_note(req.transcript)
    report = await verify_note(note, req.transcript)
    codes = await suggest_codes(note, report.flags)
    VISITS[visit_id] = {
        "status": "pending_signoff",
        "transcript": req.transcript,
        "note": note, "flags": report.flags,
        "score": report.traceability_score,
    }
    return {
        "visit_id": visit_id,
        "status": "pending_signoff",
        "note": note, "flags": report.flags,
        "traceability_score": report.traceability_score,
        "suggested_codes": codes,
        "notice": (
            "DRAFT ONLY. Not a medical record. Requires "
            "licensed clinician sign-off before use."),
    }


@app.post("/visits/{visit_id}/signoff")
async def sign_off(visit_id: str, req: SignOffRequest):
    """The only path that can ever produce a final note."""
    visit = VISITS.get(visit_id)
    if not visit or visit["status"] != "pending_signoff":
        raise HTTPException(
            404, "no draft awaiting sign-off")
    if len(req.attestation.strip()) < 20:
        raise HTTPException(
            400, "attestation must be an explicit statement")
    present = set(_claim_texts(req.edited_note))
    unresolved = [
        f for f in visit["flags"]
        if f.claim_text in present
        and f.claim_text not in req.resolved_flags]
    if unresolved:
        raise HTTPException(
            400,
            f"{len(unresolved)} flagged claim(s) neither "
            "edited nor explicitly resolved")
    visit.update({
        "status": "signed", "note": req.edited_note,
        "signed_by": req.clinician_name,
        "attestation": req.attestation})
    return {
        "visit_id": visit_id, "status": "signed",
        "note": req.edited_note}


@app.get("/visits/{visit_id}")
def get_visit(visit_id: str):
    """Only a signed note is ever returned as final."""
    visit = VISITS.get(visit_id)
    if visit is None:
        raise HTTPException(404, "unknown visit")
    if visit["status"] != "signed":
        raise HTTPException(
            409, "not yet signed off -- draft is not final")
    return {"visit_id": visit_id, "note": visit["note"]}
