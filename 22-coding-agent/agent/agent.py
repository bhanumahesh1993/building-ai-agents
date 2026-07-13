# agent/agent.py
from __future__ import annotations

from .context import build_context
from .loop import implement_and_verify
from .plan import make_plan
from .pr import open_pr_for_run
from .sandbox import create_sandbox, destroy_sandbox


async def run_issue(
    repo_url: str, base_ref: str,
    title: str, body: str,
) -> dict:
    """End to end: issue in, PR record out."""
    box = create_sandbox(repo_url, base_ref)
    try:
        ctx = build_context(box, title, body)
        plan = await make_plan(title, body, ctx)
        result, attempts = await implement_and_verify(
            box, plan, ctx.test_command)
        pr = await open_pr_for_run(
            box, plan, result, attempts)
        return {
            "pr_number": pr.number,
            "branch": pr.branch,
            "tests_passed": result.passed,
            "attempts": attempts,
            "plan": plan,
        }
    finally:
        destroy_sandbox(box)
