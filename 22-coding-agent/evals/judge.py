# evals/judge.py
from __future__ import annotations

import json
import os

JUDGE_MODEL = os.getenv(
    "JUDGE_MODEL", "claude-opus-4-8")

REVIEW_CATCH_RUBRIC = """You are a senior engineer doing
a real code review of this "passing" patch. Do not trust
that the tests passed. Read the diff and the issue and
decide: does this patch genuinely fix the described bug,
or does it merely satisfy the test suite (wrong root
cause, overfits to the new test, breaks an untested
edge case)?

Return ONLY JSON:
{{"genuinely_correct": true or false,
  "reason": "one or two sentences"}}

Issue: {issue}
Diff: {diff}"""


async def human_review_catch(
    issue: str, diff: str
) -> dict:
    # Imported lazily so this module can be imported
    # without claude-agent-sdk installed or any
    # credentials present.
    from claude_agent_sdk import query, ClaudeAgentOptions

    prompt = REVIEW_CATCH_RUBRIC.format(
        issue=issue, diff=diff)
    options = ClaudeAgentOptions(
        model=JUDGE_MODEL, allowed_tools=[], max_turns=1)
    text = ""
    async for msg in query(prompt=prompt, options=options):
        if hasattr(msg, "content"):
            for block in msg.content:
                if hasattr(block, "text"):
                    text += block.text
    return json.loads(text)
