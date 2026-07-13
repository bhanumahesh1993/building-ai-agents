# firm/state.py
from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict


class AnalystView(TypedDict):
    """One analyst's read on the symbol."""
    kind: str
    stance: Literal["bullish", "bearish", "neutral"]
    confidence: float
    rationale: str


class DebateTurn(TypedDict):
    """One turn in the bull/bear debate."""
    round: int
    side: Literal["bull", "bear"]
    argument: str


class TradeProposal(TypedDict):
    """The trader's proposed PAPER trade — never a real order."""
    action: Literal["BUY", "SELL", "HOLD"]
    size_pct: float
    stop_loss_pct: float
    thesis: str


class RiskVerdict(TypedDict):
    """The risk team's ruling on a proposal."""
    approved: bool
    adjusted_size_pct: float
    reasons: list[str]


class FirmState(TypedDict, total=False):
    """The graph's shared memory for one decision cycle."""
    symbol: str
    as_of: str
    analyst_views: Annotated[list[AnalystView], operator.add]
    debate: Annotated[list[DebateTurn], operator.add]
    debate_round: int
    max_debate_rounds: int
    proposal: TradeProposal
    risk: RiskVerdict
    risk_revisions: int
    max_risk_revisions: int
    decision: dict
    paper_fill: dict


class AnalystState(TypedDict):
    """Private state passed to one analyst."""
    kind: str
    symbol: str
    as_of: str
