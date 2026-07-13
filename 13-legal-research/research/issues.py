# research/issues.py
from __future__ import annotations

import json
import os

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions

from .prompts import ISSUE_SYSTEM

LEAD_MODEL = os.getenv(
    "LEAD_MODEL", "claude-opus-4-8")
FALLBACK = os.getenv(
    "LEAD_FALLBACK", "claude-sonnet-4-6")
MAX_ISSUES = 4


async def spot_issues(
    facts: str, jurisdiction: str) -> list[dict]:
    """Lead agent: decompose the fact pattern."""
    prompt = ISSUE_SYSTEM.format(
        facts=facts, jurisdiction=jurisdiction,
        max_issues=MAX_ISSUES,
    )
    options = ClaudeAgentOptions(
        system_prompt="You are a precise legal analyst.",
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
    raw = json.loads(text)
    return raw["issues"][:MAX_ISSUES]


if __name__ == "__main__":
    facts = (
        "An engineer signed a one-year non-compete "
        "when hired, then joined a direct competitor "
        "eight months later.")
    issues = anyio.run(spot_issues, facts, "NY")
    print(json.dumps(issues, indent=2))
