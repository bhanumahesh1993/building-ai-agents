# research/retrieval_subagent.py
from __future__ import annotations

import json
import os

from claude_agent_sdk import query, ClaudeAgentOptions

from .corpus import search_cases
from .embeddings import embed
from .prompts import RETRIEVAL_SYSTEM

WORKER_MODEL = os.getenv(
    "WORKER_MODEL", "claude-sonnet-4-6")
FALLBACK = os.getenv(
    "WORKER_FALLBACK", "claude-haiku-4-5")


async def research_issue(
    issue: dict, jurisdiction: str) -> dict:
    """One subagent: retrieve, then distil, one issue."""
    vec = embed(issue["question"])
    hits = search_cases(vec, jurisdiction, k=6)
    context = "\n\n".join(
        f"[{h['case_id']}] {h['case_name']} "
        f"({h['citation']}, {h['year']})\n"
        f"{h['chunk_text'][:1000]}"
        for h in hits
    )
    prompt = RETRIEVAL_SYSTEM.format(
        question=issue["question"], context=context,
    )
    options = ClaudeAgentOptions(
        system_prompt=(
            "You are a careful legal researcher. "
            "You never cite a case not shown to you."
        ),
        model=WORKER_MODEL,
        fallback_models=[FALLBACK],
        allowed_tools=[],
        max_turns=1,
    )
    summary = ""
    async for msg in query(prompt=prompt, options=options):
        if hasattr(msg, "content"):
            for block in msg.content:
                if hasattr(block, "text"):
                    summary += block.text
    return {
        "issue_id": issue["id"],
        "question": issue["question"],
        "summary": summary,
        "cases": hits,
    }
