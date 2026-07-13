# research/state.py
from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class ResearchTask(TypedDict):
    """One subtopic handed to a worker."""
    topic: str
    goal: str


class Finding(TypedDict):
    """A single worker's distilled result."""
    topic: str
    summary: str
    sources: list[dict]


class ReportState(TypedDict, total=False):
    """The graph's shared memory."""
    question: str
    plan: list[ResearchTask]
    approved: bool
    findings: Annotated[list[Finding], operator.add]
    draft: str
    report: str
    loops: int
    max_loops: int


class WorkerState(TypedDict):
    """Private state passed to one worker."""
    task: ResearchTask
    question: str
