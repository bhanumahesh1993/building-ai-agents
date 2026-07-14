# tests/conftest.py
"""Shared deterministic fakes for the trading-firm test suite.

Every test in this package runs fully offline: no ANTHROPIC_API_KEY,
no network call, no brokerage of any kind. Each firm.nodes.* module
builds its LangChain client lazily behind a module-level `_get_llm()`
function (see e.g. firm/nodes/risk.py), so tests patch that function
directly rather than instantiating a real ChatAnthropic client."""
from __future__ import annotations

import json

from firm.nodes import analysts as analysts_mod
from firm.nodes import debate as debate_mod
from firm.nodes import manager as manager_mod
from firm.nodes import risk as risk_mod
from firm.nodes import trader as trader_mod


class FakeResponse:
    """Stands in for a LangChain AIMessage: only `.content` is read."""
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    """Returns a fixed `.content` string for every `.invoke()` call —
    no network, fully deterministic."""
    def __init__(self, content: str):
        self._content = content

    def invoke(self, prompt):
        return FakeResponse(self._content)


def analyst_llm(stance: str = "bullish", confidence: float = 0.7) -> FakeLLM:
    return FakeLLM(json.dumps({
        "stance": stance, "confidence": confidence,
        "rationale": "Grounded in the synthetic payload.",
    }))


def debate_llm(argument: str = "A specific, grounded argument.") -> FakeLLM:
    # bull_node/bear_node use resp.content directly as plain text,
    # not JSON.
    return FakeLLM(argument)


def trader_llm(action: str = "BUY", size_pct: float = 0.02,
               stop_loss_pct: float = 0.02) -> FakeLLM:
    return FakeLLM(json.dumps({
        "action": action, "size_pct": size_pct,
        "stop_loss_pct": stop_loss_pct,
        "thesis": "Bull case beat the strongest bear point.",
    }))


def risk_llm(approved: bool = True, adjusted_size_pct: float = 0.02,
             reasons: list[str] | None = None) -> FakeLLM:
    return FakeLLM(json.dumps({
        "approved": approved,
        "adjusted_size_pct": adjusted_size_pct,
        "reasons": reasons or ["within limits"],
    }))


def manager_llm(action: str = "BUY", size_pct: float = 0.02) -> FakeLLM:
    return FakeLLM(json.dumps({
        "action": action, "size_pct": size_pct,
        "rationale": "Risk-adjusted size, debate engaged both sides.",
    }))


def patch_all_llms(
    monkeypatch, *,
    trader_action: str = "BUY", trader_size: float = 0.02,
    risk_approved: bool = True, risk_adjusted_size: float = 0.02,
    manager_action: str = "BUY", manager_size: float = 0.02,
) -> None:
    """Patch every node's `_get_llm` with a deterministic fake so a
    real graph run never touches the network or needs a key."""
    monkeypatch.setattr(
        analysts_mod, "_get_llm", lambda: analyst_llm())
    monkeypatch.setattr(
        debate_mod, "_get_llm", lambda: debate_llm())
    monkeypatch.setattr(
        trader_mod, "_get_llm",
        lambda: trader_llm(action=trader_action, size_pct=trader_size))
    monkeypatch.setattr(
        risk_mod, "_get_llm",
        lambda: risk_llm(approved=risk_approved,
                          adjusted_size_pct=risk_adjusted_size))
    monkeypatch.setattr(
        manager_mod, "_get_llm",
        lambda: manager_llm(action=manager_action, size_pct=manager_size))
