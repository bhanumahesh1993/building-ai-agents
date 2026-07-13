# scribe/models.py
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Confidence = Literal["high", "medium", "low"]
Section = Literal[
    "subjective", "objective", "assessment", "plan"]


class Provenance(BaseModel):
    """Exactly where in the transcript a claim comes
    from -- never optional once a claim asserts a fact."""
    quote: str = Field(
        max_length=240,
        description="verbatim excerpt from the cited turn")
    speaker: Literal["patient", "clinician", "unknown"]
    turn_index: int = Field(ge=0)


class ClinicalClaim(BaseModel):
    """One line of the note, tied to its source."""
    text: str
    provenance: Provenance | None = Field(
        default=None,
        description="omit only if no turn supports this")


class SOAPNote(BaseModel):
    """The four-part note a clinician expects to sign."""
    subjective: list[ClinicalClaim] = Field(min_length=1)
    objective: list[ClinicalClaim] = Field(
        default_factory=list)
    assessment: list[ClinicalClaim] = Field(min_length=1)
    plan: list[ClinicalClaim] = Field(min_length=1)


class ICDCode(BaseModel):
    """One suggested billing code -- never auto-applied."""
    code: str = Field(
        pattern=r"^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$")
    description: str
    supporting_text: str
    confidence: Confidence


class ICDSuggestions(BaseModel):
    codes: list[ICDCode]


class TraceabilityFlag(BaseModel):
    """One claim the verifier could not confirm."""
    section: Section
    claim_text: str
    reason: str


class FlagList(BaseModel):
    """Raw output of the LLM half of verification."""
    flags: list[TraceabilityFlag]


class TraceabilityReport(BaseModel):
    """Combined heuristic + LLM verification result."""
    flags: list[TraceabilityFlag]
    traceability_score: float = Field(ge=0.0, le=1.0)
