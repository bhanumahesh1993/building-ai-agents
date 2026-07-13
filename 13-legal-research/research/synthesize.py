# research/synthesize.py
from __future__ import annotations

import json
import os

from claude_agent_sdk import query, ClaudeAgentOptions

from .prompts import SYNTH_SYSTEM

LEAD_MODEL = os.getenv(
    "LEAD_MODEL", "claude-opus-4-8")
FALLBACK = os.getenv(
    "LEAD_FALLBACK", "claude-sonnet-4-6")


async def synthesize_issue(finding: dict) -> dict:
    """Lead agent: for/against argument for one issue."""
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
    return json.loads(text)
