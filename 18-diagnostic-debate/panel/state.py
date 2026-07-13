# panel/state.py
from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

Bias = Literal[
    "anchoring", "premature_closure", "confirmation"]
Stance = Literal["support", "challenge"]
Status = Literal["active", "retired"]


class Hypothesis(TypedDict):
    """One candidate diagnosis under debate."""
    name: str
    rationale: str
    confidence: float
    status: Status


class Argument(TypedDict):
    """One advocate's case for or against a hypothesis."""
    hypothesis: str
    stance: Stance
    text: str
    round: int


class TestOrder(TypedDict):
    """One test the panel wants, and its price tag."""
    test: str
    rationale: str
    cost_usd: float


class BiasFlag(TypedDict):
    """One thing the independent checker did not like."""
    kind: Bias
    target: str
    note: str


class PanelState(TypedDict, total=False):
    """The graph's shared whiteboard."""
    vignette: str
    available_results: dict[str, str]
    revealed_results: dict[str, str]
    findings: list[str]
    orders: list[TestOrder]
    cost_total: float
    cost_cap: float
    hypotheses: list[Hypothesis]
    arguments: Annotated[list[Argument], operator.add]
    round: int
    max_rounds: int
    bias_flags: list[BiasFlag]
    bias_rechecks: int
    force_recheck: bool
    final_differential: list[Hypothesis]
    cost_note: str
    approved: bool


class AdvocateState(TypedDict):
    """Private state passed to one hypothesis advocate."""
    hypothesis: Hypothesis
    rivals: list[Hypothesis]
    findings: list[str]
    revealed_results: dict[str, str]
    round: int
