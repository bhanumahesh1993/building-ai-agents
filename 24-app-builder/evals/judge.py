# evals/judge.py
from __future__ import annotations

import json
import os

from claude_agent_sdk import query, ClaudeAgentOptions

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "claude-opus-4-8")

RUBRIC = """Grade this generated app against its spec.
Score 1-5 (5 best). Return JSON only.

- scope_discipline: did it avoid building anything the
  non_goals ruled out, or anything the spec never asked
  for?
- code_plausibility: does the code look like it would
  actually run, structurally?

Non-goals: {non_goals}
Generated CLAUDE.md: {claude_md}

JSON: {{"scope_discipline": n,
"code_plausibility": n, "notes": "..."}}"""


async def grade(non_goals: list[str], claude_md: str):
    prompt = RUBRIC.format(
        non_goals=non_goals, claude_md=claude_md)
    options = ClaudeAgentOptions(
        model=JUDGE_MODEL, allowed_tools=[], max_turns=1)
    text = ""
    async for msg in query(prompt=prompt, options=options):
        if hasattr(msg, "content"):
            for block in msg.content:
                if hasattr(block, "text"):
                    text += block.text
    return json.loads(text)
