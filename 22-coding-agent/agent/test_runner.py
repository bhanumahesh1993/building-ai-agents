# agent/test_runner.py
from __future__ import annotations

from dataclasses import dataclass

from .sandbox import Sandbox


@dataclass
class TestResult:
    passed: bool
    summary: str
    raw_output: str


def run_tests(
    box: Sandbox, test_command: str
) -> TestResult:
    """Run the real suite inside the sandbox. No mocking."""
    cmd = test_command.split()
    result = box.run(cmd, timeout=180)
    output = result.stdout + result.stderr
    passed = result.returncode == 0
    summary = _summarize(output, passed)
    return TestResult(
        passed=passed, summary=summary,
        raw_output=output[-4000:],
    )


def _summarize(output: str, passed: bool) -> str:
    lines = [ln for ln in output.splitlines()
             if "passed" in ln or "failed" in ln
             or "error" in ln.lower()]
    tail = "\n".join(lines[-5:]) or output[-300:]
    verdict = "PASSED" if passed else "FAILED"
    return f"{verdict}\n{tail}"
