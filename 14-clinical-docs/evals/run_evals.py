# evals/run_evals.py
from __future__ import annotations

import json

from scribe.coding import suggest_codes
from scribe.extract import extract_note
from scribe.verify import verify_note

from .judge import hallucination_rate


def completeness(note, gold_facts: list[str]) -> float:
    text = " ".join(
        c.text.lower() for s in
        ("subjective", "objective", "assessment", "plan")
        for c in getattr(note, s))
    hits = sum(
        1 for g in gold_facts if g.lower() in text)
    return hits / max(len(gold_facts), 1)


async def run_one(case: dict) -> dict:
    with open(case["transcript_file"]) as fh:
        transcript = fh.read()
    note = await extract_note(transcript)
    report = await verify_note(note, transcript)
    codes = await suggest_codes(note, report.flags)
    kept = [
        c.text for s in
        ("subjective", "objective", "assessment", "plan")
        for c in getattr(note, s)
        if c.text not in
        {f.claim_text for f in report.flags}]
    halluc = await hallucination_rate(transcript, kept)
    code_set = {c.code[:3] for c in codes}
    expected = set(case["expected_codes"])
    overlap = len(code_set & expected) / max(
        len(expected), 1)
    return {
        "completeness": completeness(
            note, case["gold_facts"]),
        "traceability_score": report.traceability_score,
        "code_overlap": overlap,
        "hallucinations_missed":
            halluc.unsupported_count,
    }
