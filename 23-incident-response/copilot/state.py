# copilot/state.py
from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class Alert(TypedDict):
    """A normalized alert. raw is fenced, never bare."""
    alert_id: str
    service: str
    signal: str
    severity: str
    raw: str
    started_at: str


class Investigation(TypedDict):
    """One worker's read-only contribution."""
    kind: str
    summary: str


class RootCause(TypedDict):
    """The root-cause node's opinion. No tools attached."""
    hypothesis: str
    confidence: float
    evidence: list[str]
    category: str


class Remediation(TypedDict):
    """A retrieved runbook mapped to a proposed action."""
    runbook_id: str
    steps: list[str]
    action: str
    blast_radius: str


class IncidentState(TypedDict, total=False):
    """The graph's shared memory for one incident."""
    raw_alert: dict
    alert: Alert
    investigations: Annotated[
        list[Investigation], operator.add]
    root_cause: RootCause
    remediation: Remediation
    resolution: str
    action_result: str
    audit: Annotated[list[dict], operator.add]


class WorkerState(TypedDict):
    """Private state for one investigation worker."""
    alert: Alert
    kind: str
