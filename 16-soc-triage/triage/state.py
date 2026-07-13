# triage/state.py
from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class Alert(TypedDict):
    """A normalized alert. raw is fenced, never bare."""
    alert_id: str
    source: str
    rule_name: str
    severity: str
    raw: str
    entities: dict


class EnrichmentResult(TypedDict):
    """One worker's read-only contribution."""
    kind: str
    summary: str


class Verdict(TypedDict):
    """The verdict node's opinion. No tools attached."""
    label: str
    confidence: float
    evidence: list[str]
    recommended_action: str


class TriageState(TypedDict, total=False):
    """The graph's shared memory for one alert."""
    raw_event: dict
    alert: Alert
    enrichment: Annotated[
        list[EnrichmentResult], operator.add]
    related_alerts: list[str]
    pattern_notes: str
    verdict: Verdict
    resolution: str
    action_result: str
    audit: Annotated[list[dict], operator.add]


class WorkerState(TypedDict):
    """Private state handed to one enrichment worker."""
    alert: Alert
    kind: str
