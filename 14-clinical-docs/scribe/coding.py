# scribe/coding.py
from __future__ import annotations

import os

from pydantic_ai import Agent

from .models import ICDCode, ICDSuggestions, SOAPNote
from .models import TraceabilityFlag
from .prompts import CODE_SYSTEM

CODE_MODEL = os.getenv(
    "CODE_MODEL", "anthropic:claude-haiku-4-5")

coding_agent = Agent(
    CODE_MODEL, output_type=ICDSuggestions)


async def suggest_codes(
        note: SOAPNote,
        flags: list[TraceabilityFlag],
) -> list[ICDCode]:
    """Suggest ICD-10 codes from VERIFIED lines only."""
    flagged = {f.claim_text for f in flags}
    verified = [
        c.text for c in note.assessment
        if c.text not in flagged]
    if not verified:
        return []
    prompt = CODE_SYSTEM.format(
        assessment="\n".join(f"- {t}" for t in verified))
    result = await coding_agent.run(prompt)
    return result.output.codes
