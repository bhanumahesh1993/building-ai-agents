# research/synthesize.py
from __future__ import annotations

import json
import os

from .prompts import SYNTH_SYSTEM

LEAD_MODEL = os.getenv(
    "LEAD_MODEL", "claude-opus-4-8")
FALLBACK = os.getenv(
    "LEAD_FALLBACK", "claude-sonnet-4-6")

REQUIRED_KEYS = (
    "issue_id", "for", "for_cites",
    "against", "against_cites", "weight",
)


def _parse_synthesis_response(text: str) -> dict:
    """Pure argument-balance validation: parse the lead
    agent's JSON reply and enforce that both sides of the
    argument (and their citations) are present. Factored
    out so this contract is unit-testable without the
    Claude Agent SDK or any live model call."""
    parsed = json.loads(text)
    missing = [k for k in REQUIRED_KEYS if k not in parsed]
    if missing:
        raise ValueError(
            f"synthesis response missing keys: {missing}")
    if not parsed["for"].strip() or not parsed["against"].strip():
        raise ValueError(
            "synthesis response must argue both sides")
    return parsed


async def synthesize_issue(finding: dict) -> dict:
    """Lead agent: for/against argument for one issue."""
    # Imported lazily so this module can be imported (and
    # its pure argument-balance validation tested) without
    # claude-agent-sdk installed or any credentials present.
    from claude_agent_sdk import query, ClaudeAgentOptions

    prompt = SYNTH_SYSTEM.format(
        issue_id=finding["issue_id"],
        findings=finding["summary"],
    )
    options = ClaudeAgentOptions(
        system_prompt=(
            "You are a senior associate. Argue both "
            "sides honestly; never invent authority."
        ),
        model=LEAD_MODEL,
        fallback_models=[FALLBACK],
        allowed_tools=[],
        max_turns=1,
    )
    text = ""
    async for msg in query(prompt=prompt, options=options):
        if hasattr(msg, "content"):
            for block in msg.content:
                if hasattr(block, "text"):
                    text += block.text
    return _parse_synthesis_response(text)
