# support/state.py
from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class KBHit(TypedDict):
    """One retrieved knowledge-base passage."""
    doc: str
    section: str
    url: str
    body: str


class Escalation(TypedDict):
    """Structured handoff summary for a human agent."""
    issue: str
    attempted: str
    sentiment: str
    urgency: str
    queue: str


class TicketState(TypedDict, total=False):
    """The graph's shared whiteboard for one ticket."""
    ticket_id: str
    customer_id: str
    message: str
    category: str
    confidence: float
    kb_hits: list[KBHit]
    answer: str
    citations: list[str]
    grounded: bool
    escalation: Escalation
    resolution: str
    events: Annotated[list[dict], operator.add]
