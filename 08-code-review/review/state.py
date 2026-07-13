# review/state.py
from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

Severity = Literal["critical", "high", "medium", "low"]


class Hunk(TypedDict):
    """One changed region of one file."""
    path: str
    start_line: int
    end_line: int
    patch: str


class Finding(TypedDict):
    """One reviewer's claim about the diff."""
    reviewer: str
    path: str
    line: int
    severity: Severity
    claim: str
    evidence: str


class VerifiedFinding(TypedDict):
    """A finding after adversarial refutation."""
    finding: Finding
    verdict: Literal["confirmed", "refuted"]
    rationale: str


class ReviewState(TypedDict, total=False):
    """The graph's shared memory for one PR review."""
    pr_id: str
    diff: str
    hunks: list[Hunk]
    truncated: bool
    findings: Annotated[list[Finding], operator.add]
    verified: Annotated[list[VerifiedFinding], operator.add]
    report: str
    decision: str


class ReviewerState(TypedDict):
    """Private state passed to one specialist."""
    role: str
    hunks: list[Hunk]
    pr_id: str


class VerifierState(TypedDict):
    """Private state passed to one verifier call."""
    finding: Finding
    context: str
