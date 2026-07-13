# tests/test_verify.py
from scribe.models import (
    ClinicalClaim, Provenance, SOAPNote)
from scribe.verify import heuristic_flags

TURNS = [
    "Pt: knee pain for three weeks",
    "Dr: any swelling or fever?",
    "Pt: mild swelling, no fever",
]


def test_missing_provenance_is_flagged():
    note = SOAPNote(
        subjective=[ClinicalClaim(text="fever present")],
        assessment=[ClinicalClaim(text="likely strain")],
        plan=[ClinicalClaim(text="NSAIDs")])
    flags = heuristic_flags(note, TURNS)
    assert len(flags) == 3


def test_supported_quote_passes():
    prov = Provenance(
        quote="knee pain for three weeks",
        speaker="patient", turn_index=0)
    note = SOAPNote(
        subjective=[ClinicalClaim(
            text="knee pain x3 weeks", provenance=prov)],
        assessment=[ClinicalClaim(
            text="likely strain", provenance=prov)],
        plan=[ClinicalClaim(
            text="NSAIDs", provenance=prov)])
    assert heuristic_flags(note, TURNS) == []
