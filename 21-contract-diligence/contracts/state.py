# contracts/state.py
from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

ClauseType = Literal[
    "indemnification", "liability_cap", "termination",
    "ip_assignment", "confidentiality", "governing_law",
    "other",
]
Severity = Literal["low", "medium", "high"]


class ContractDoc(TypedDict):
    """One parsed file in the document set."""
    contract_id: str
    filename: str
    text: str


class Clause(TypedDict):
    """One typed, located clause."""
    clause_id: str
    contract_id: str
    clause_type: ClauseType
    heading: str
    text: str


class RiskFlag(TypedDict):
    """A specialist's risk call on one clause."""
    clause_id: str
    clause_type: ClauseType
    severity: Severity
    quote: str
    rationale: str


class GroundedFlag(TypedDict):
    """A risk flag, grounded against the playbook."""
    clause_id: str
    clause_type: ClauseType
    severity: Severity
    quote: str
    rationale: str
    deviation: str
    playbook_ref: str


class Redline(TypedDict):
    """A proposed edit with a rationale."""
    clause_id: str
    proposed_text: str
    rationale: str


class DDState(TypedDict, total=False):
    """The graph's shared memory: the whole matter."""
    matter_id: str
    doc_folder: str
    jurisdiction: str
    contracts: list[ContractDoc]
    clauses: Annotated[list[Clause], operator.add]
    flags: Annotated[list[RiskFlag], operator.add]
    grounded: Annotated[list[GroundedFlag], operator.add]
    redlines: Annotated[list[Redline], operator.add]
    memo: str
    reviewed: bool


class RiskWorkerState(TypedDict):
    """Private state for one clause-type specialist."""
    clause_type: ClauseType
    clauses: list[Clause]


class PlaybookWorkerState(TypedDict):
    """Private state for one grounding call."""
    flag: RiskFlag
    clause: Clause
    jurisdiction: str
