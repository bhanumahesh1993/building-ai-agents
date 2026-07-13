# evals/run_evals.py
from __future__ import annotations

import json

from builder.agent import run_build
from builder.spec import AppSpec, AcceptanceCriterion
from .judge import grade


async def run_one(row: dict) -> dict:
    spec = AppSpec(
        name=row["name"], goal=row["goal"],
        acceptance_criteria=[AcceptanceCriterion(
            id="AC-1", pattern="ubiquitous",
            response="persist the primary entity")],
        non_goals=["no user accounts", "no payments"])
    result = await run_build(spec)
    total = len(result.verify.passed) or 1
    passed = sum(result.verify.passed.values())
    claude_md = (result.root / "CLAUDE.md").read_text()
    scores = await grade(spec.non_goals, claude_md)
    return {
        "name": row["name"],
        "acceptance_pass_rate": passed / total,
        "build_success": result.ready,
        "iterations": result.iterations,
        **scores,
    }


if __name__ == "__main__":
    import asyncio
    with open("evals/dataset.jsonl") as fh:
        rows = [json.loads(line) for line in fh]
    for row in rows:
        print(asyncio.run(run_one(row)))
