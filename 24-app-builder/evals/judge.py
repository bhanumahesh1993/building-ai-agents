# evals/judge.py
from __future__ import annotations

import json
import os

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


def _parse_grade_response(text: str) -> dict:
    """Pure parsing logic: the judge's JSON reply as a
    dict. Factored out so the rubric shape is
    unit-testable without the Claude Agent SDK or any
    live model call."""
    return json.loads(text)


async def grade(non_goals: list[str], claude_md: str):
    # Imported lazily so this module can be imported (and
    # its pure parsing logic tested) without claude-agent-sdk
    # installed or any credentials present.
    from claude_agent_sdk import query, ClaudeAgentOptions

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
    return _parse_grade_response(text)
