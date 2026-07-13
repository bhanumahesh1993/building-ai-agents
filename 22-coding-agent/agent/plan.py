# agent/plan.py
from __future__ import annotations

import json
import os

from claude_agent_sdk import query, ClaudeAgentOptions

from .context import RepoContext
from .prompts import PLAN_SYSTEM

LEAD_MODEL = os.getenv(
    "LEAD_MODEL", "claude-opus-4-8")
FALLBACK = os.getenv(
    "LEAD_FALLBACK", "claude-sonnet-4-6")


async def make_plan(
    title: str, body: str, ctx: RepoContext
) -> dict:
    """Lead agent: decide the approach, write no code."""
    files_block = "\n\n".join(
        f"# {path}\n{text}"
        for path, text in ctx.relevant_files.items())
    prompt = PLAN_SYSTEM.format(
        title=title, body=body, tree=ctx.tree,
        files=files_block,
    )
    options = ClaudeAgentOptions(
        system_prompt="You are a careful senior engineer.",
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
