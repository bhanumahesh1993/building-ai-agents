# research/citations.py
from __future__ import annotations

import json
import os

from claude_agent_sdk import query, ClaudeAgentOptions

from .corpus import case_exists, case_full_text
from .prompts import CITE_VERIFY_SYSTEM

JUDGE_MODEL = os.getenv(
    "JUDGE_MODEL", "claude-opus-4-8")


async def _tier2_supports(claim: str, case_id: str) -> bool:
    """Does the case's actual text support this claim?"""
    full_text = case_full_text(case_id)
    prompt = CITE_VERIFY_SYSTEM.format(
        claim=claim, case_text=full_text[:6000],
    )
    options = ClaudeAgentOptions(
        system_prompt="You are a strict cite-checker.",
        model=JUDGE_MODEL, allowed_tools=[], max_turns=1,
    )
    text = ""
    async for msg in query(prompt=prompt, options=options):
        if hasattr(msg, "content"):
            for block in msg.content:
                if hasattr(block, "text"):
                    text += block.text
    return json.loads(text)["supported"]


async def verify_citations(cites: list[dict]) -> list[dict]:
    """Verify-or-strip: every citation, two tiers, no
    exceptions."""
    verified: list[dict] = []
    for c in cites:
        record = case_exists(c["case_id"])
        if record is None:
            # Tier 1 fails: not a real case. Non-
            # negotiable — strip, never soften.
            verified.append({**c, "status": "stripped",
                              "reason": "case not found "
                              "in corpus"})
            continue
        supported = await _tier2_supports(
            c["claim"], c["case_id"])
        if not supported:
            verified.append({**c, "status": "flagged",
                              "reason": "case exists but "
                              "does not clearly support "
                              "this claim",
                              "citation": record["citation"]})
        else:
            verified.append({**c, "status": "verified",
                              "citation": record["citation"],
                              "case_name": record["case_name"]})
    return verified
