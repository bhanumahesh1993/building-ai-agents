# scribe/extract.py
from __future__ import annotations

import os

from pydantic_ai import Agent

from .models import SOAPNote
from .prompts import EXTRACT_SYSTEM

EXTRACT_MODEL = os.getenv(
    "EXTRACT_MODEL", "anthropic:claude-sonnet-4-5")

_extract_agent: Agent | None = None


def get_extract_agent() -> Agent:
    """Lazily build so the module imports without a key present."""
    global _extract_agent
    if _extract_agent is None:
        _extract_agent = Agent(
            EXTRACT_MODEL, output_type=SOAPNote)
    return _extract_agent


def _numbered(transcript: str) -> str:
    lines = transcript.splitlines()
    return "\n".join(
        f"[{i}] {line}" for i, line in enumerate(lines))


async def extract_note(transcript: str) -> SOAPNote:
    """Turn a visit transcript into a typed SOAP note."""
    prompt = EXTRACT_SYSTEM.format(
        transcript=_numbered(transcript))
    result = await get_extract_agent().run(prompt)
    return result.output
