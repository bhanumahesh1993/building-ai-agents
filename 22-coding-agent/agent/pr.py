# agent/pr.py
from __future__ import annotations

import os
import subprocess

from claude_agent_sdk import query, ClaudeAgentOptions

from .github_stub import open_pull_request, PullRequest
from .prompts import PR_SYSTEM
from .sandbox import Sandbox
from .test_runner import TestResult

LEAD_MODEL = os.getenv(
    "LEAD_MODEL", "claude-opus-4-8")


def _diff_summary(box: Sandbox) -> str:
    res = box.run(["git", "diff", "--stat", "HEAD"])
    return res.stdout.strip() or "(no diff produced)"


async def open_pr_for_run(
    box: Sandbox, plan: dict, result: TestResult,
    attempts: int,
) -> PullRequest:
    """Package plan + diff + test verdict into a PR."""
    diff_stat = _diff_summary(box)
    diff_full = box.run(
        ["git", "diff", "HEAD"]).stdout[:6000]
    verdict = "passed" if result.passed else "STILL FAILING"
    test_summary = (
        f"{verdict} after {attempts} attempt(s)\n"
        f"{result.summary}")
    prompt = PR_SYSTEM.format(
        approach=plan["approach"],
        diff_summary=diff_stat,
        test_summary=test_summary,
    )
    options = ClaudeAgentOptions(
        system_prompt="You write honest PR descriptions.",
        model=LEAD_MODEL, allowed_tools=[], max_turns=1,
    )
    body = ""
    async for msg in query(prompt=prompt, options=options):
        if hasattr(msg, "content"):
            for block in msg.content:
                if hasattr(block, "text"):
                    body += block.text
    title = f"fix: {plan['approach'][:60]}"
    return open_pull_request(
        title=title, body=body, branch=box.branch,
        diff=diff_full,
    )
