# agent/loop.py
from __future__ import annotations

from .implement import implement_plan, fix_failure
from .sandbox import Sandbox
from .test_runner import run_tests, TestResult

MAX_RETRIES = 3


async def implement_and_verify(
    box: Sandbox, plan: dict, test_command: str
) -> tuple[TestResult, int]:
    """Implement, then loop test -> fix, capped."""
    await implement_plan(box, plan)
    result = run_tests(box, test_command)
    attempts = 1
    while not result.passed and attempts <= MAX_RETRIES:
        await fix_failure(box, result.raw_output)
        result = run_tests(box, test_command)
        attempts += 1
    return result, attempts
