# scribe/verify.py
from __future__ import annotations

import difflib
import os

from pydantic_ai import Agent

from .models import FlagList, SOAPNote, TraceabilityFlag
from .models import TraceabilityReport
from .prompts import VERIFY_SYSTEM

VERIFY_MODEL = os.getenv(
    "VERIFY_MODEL", "anthropic:claude-sonnet-4-5")

verify_agent = Agent(VERIFY_MODEL, output_type=FlagList)

SECTIONS = (
    "subjective", "objective", "assessment", "plan")


def _quote_supported(quote: str, turn: str) -> bool:
    """Cheap check: does the cited turn contain it?"""
    ratio = difflib.SequenceMatcher(
        None, quote.lower(), turn.lower()).ratio()
    return quote.lower() in turn.lower() or ratio > 0.6


def heuristic_flags(
        note: SOAPNote, turns: list[str],
) -> list[TraceabilityFlag]:
    """Code-level first pass: no quote, no pass."""
    flags: list[TraceabilityFlag] = []
    for section in SECTIONS:
        for claim in getattr(note, section):
            prov = claim.provenance
            if prov is None:
                flags.append(TraceabilityFlag(
                    section=section, claim_text=claim.text,
                    reason="no provenance attached"))
                continue
            if prov.turn_index >= len(turns):
                flags.append(TraceabilityFlag(
                    section=section, claim_text=claim.text,
                    reason="turn_index out of range"))
                continue
            cited = turns[prov.turn_index]
            if not _quote_supported(prov.quote, cited):
                flags.append(TraceabilityFlag(
                    section=section, claim_text=claim.text,
                    reason="quote not found in cited turn"))
    return flags


async def verify_note(
        note: SOAPNote, transcript: str,
) -> TraceabilityReport:
    """Two-pass check: code quote-match, then meaning."""
    turns = transcript.splitlines()
    code_flags = heuristic_flags(note, turns)
    already_flagged = {f.claim_text for f in code_flags}
    claims_desc = "\n".join(
        f"- [{section}] {c.text}"
        for section in SECTIONS
        for c in getattr(note, section)
        if c.text not in already_flagged)
    prompt = VERIFY_SYSTEM.format(
        claims=claims_desc, transcript=transcript)
    llm_result = await verify_agent.run(prompt)
    all_flags = code_flags + llm_result.output.flags
    total = sum(
        len(getattr(note, s)) for s in SECTIONS)
    score = 1.0 - (len(all_flags) / max(total, 1))
    return TraceabilityReport(
        flags=all_flags,
        traceability_score=max(score, 0.0))
