# tests/test_gate.py
from __future__ import annotations


class FakeVerify:
    def __init__(self, passing: set[str]) -> None:
        self.passing = passing
        self.passed = {
            c: (c in passing) for c in ("AC-1", "AC-3")}

    @property
    def all_passed(self) -> bool:
        return all(self.passed.values())

    def failing(self) -> list[str]:
        return [c for c, ok in self.passed.items()
                if not ok]


def run_gate(max_iterations: int, always_fails: bool):
    """Mirror agent.py's loop shape with no real I/O."""
    attempts = 0
    for i in range(max_iterations + 1):
        passing = set() if always_fails else {
            "AC-1", "AC-3"}
        verify = FakeVerify(passing)
        attempts = i
        if verify.all_passed or i == max_iterations:
            return verify, attempts
    return verify, attempts


def test_stops_at_cap_when_unfixable():
    verify, attempts = run_gate(
        max_iterations=2, always_fails=True)
    assert attempts == 2
    assert not verify.all_passed


def test_succeeds_before_cap_when_fixable():
    verify, attempts = run_gate(
        max_iterations=2, always_fails=False)
    assert attempts == 0
    assert verify.all_passed
