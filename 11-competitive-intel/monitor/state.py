# monitor/state.py
from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class Snapshot(TypedDict):
    """One fetch of one page at one point in time."""
    url: str
    competitor: str
    kind: str
    text: str
    fetched_at: str


class ChangeRecord(TypedDict):
    """A page that changed, with the diff explained."""
    url: str
    competitor: str
    kind: str
    summary: str
    changed: bool
    evidence: str


class ScoredChange(TypedDict):
    """A change record plus its significance score."""
    url: str
    competitor: str
    kind: str
    summary: str
    score: int
    reason: str


class MonitorState(TypedDict, total=False):
    """The graph's shared memory for one scheduled run."""
    run_id: str
    changes: Annotated[list[ChangeRecord], operator.add]
    scored: Annotated[list[ScoredChange], operator.add]
    digest: str
    max_targets: int
    min_score: int


class WorkerState(TypedDict):
    """Private state passed to one fetch worker."""
    url: str
    competitor: str
    kind: str
    content_selector: str
