# aml/state.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CaseStatus(str, Enum):
    """Where a case sits. There is no FILED value --
    only a human, outside this system, makes that true."""
    NEW = "new"
    INVESTIGATING = "investigating"
    SCORED = "scored"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Transaction:
    txn_id: str
    account_id: str
    counterparty: str
    amount: float
    ts: datetime
    memo: str


@dataclass
class Alert:
    """One rule or anomaly signal that fired."""
    rule: str
    reason: str
    txn_ids: list[str]


@dataclass
class Entity:
    """A KYC-resolved party, possibly merging aliases."""
    entity_id: str
    display_name: str
    aliases: list[str]
    risk_tier: str  # "low" | "medium" | "high"


@dataclass
class Evidence:
    """One citable fact backing a score or a claim."""
    claim: str
    txn_ids: list[str]
    source: str  # "rule" | "anomaly" | "investigation"


@dataclass
class TypologyMatch:
    name: str          # "structuring" | "layering"
    confidence: float  # 0-1
    evidence: list[Evidence]


@dataclass
class Case:
    """The one file every stage reads and appends to."""
    case_id: str
    subject_account: str
    status: CaseStatus = CaseStatus.NEW
    alerts: list[Alert] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    narrative: str = ""
    typologies: list[TypologyMatch] = field(
        default_factory=list)
    risk_score: float = 0.0
    sar_draft: str = ""
    audit_log: list[str] = field(default_factory=list)

    def log(self, event: str) -> None:
        stamp = datetime.utcnow().isoformat(
            timespec="seconds")
        self.audit_log.append(f"{stamp} {event}")
