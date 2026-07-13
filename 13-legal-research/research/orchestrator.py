# research/orchestrator.py
from __future__ import annotations

import anyio

from .issues import spot_issues
from .retrieval_subagent import research_issue


async def run_research(
    facts: str, jurisdiction: str) -> dict:
    """Spot issues, then fan out one subagent each."""
    issues = await spot_issues(facts, jurisdiction)
    findings: list[dict] = []

    async def worker(issue: dict) -> None:
        finding = await research_issue(
            issue, jurisdiction)
        findings.append(finding)

    async with anyio.create_task_group() as tg:
        for issue in issues:
            tg.start_soon(worker, issue)

    return {
        "facts": facts,
        "jurisdiction": jurisdiction,
        "issues": issues,
        "findings": findings,
    }
