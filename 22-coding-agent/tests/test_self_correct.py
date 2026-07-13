# tests/test_self_correct.py
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from agent.loop import implement_and_verify
from agent.test_runner import TestResult


def test_loop_caps_and_reports_failure():
    """Never-passing tests must not loop forever."""
    always_fails = TestResult(
        passed=False, summary="FAILED\n1 failed",
        raw_output="AssertionError: nope",
    )
    with patch(
        "agent.loop.implement_plan", new=AsyncMock()
    ), patch(
        "agent.loop.fix_failure", new=AsyncMock()
    ), patch(
        "agent.loop.run_tests",
        return_value=always_fails,
    ):
        result, attempts = asyncio.run(
            implement_and_verify(
                box=object(), plan={},
                test_command="pytest -q"))
    assert attempts == 4          # 1 initial + 3 retries
    assert result.passed is False  # reported, not hidden
