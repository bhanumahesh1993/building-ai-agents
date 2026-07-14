# tests/test_no_live_trading.py
"""The no-live-trading guard is a structural property of this
codebase, not a prompt instruction: there is no brokerage client
anywhere in `firm/`, every simulated fill hard-codes
`broker_order_id: None` in source (never computed from a model's
output), and the position-size cap is clamped by `min()` in
`firm/nodes/risk.py`'s own code, not merely asked for in a prompt.
These tests prove that statically (reading the source) and
dynamically (feeding an adversarial LLM output through the real
node functions)."""
from __future__ import annotations

import inspect

from firm.nodes import manager as manager_mod
from firm.nodes import risk as risk_mod

from .conftest import manager_llm, risk_llm

# SDK/package names for real brokerages or live order-routing —
# none of these may ever appear in the firm package's source.
FORBIDDEN_BROKER_TOKENS = (
    "alpaca", "ib_insync", "ibapi", "ccxt", "robinhood",
    "tradestation", "interactive_brokers", "td_ameritrade",
    "schwab", "webull", "coinbase", "binance",
)


def _all_firm_source() -> str:
    import firm
    import firm.app
    import firm.data
    import firm.graph
    import firm.nodes.analysts
    import firm.nodes.debate
    import firm.nodes.manager
    import firm.nodes.risk
    import firm.nodes.trader

    modules = [
        firm, firm.app, firm.data, firm.graph,
        firm.nodes.analysts, firm.nodes.debate,
        firm.nodes.manager, firm.nodes.risk, firm.nodes.trader,
    ]
    return "\n".join(inspect.getsource(m) for m in modules)


def test_no_brokerage_sdk_is_imported_or_named_anywhere():
    """Static check: no real brokerage/exchange SDK is imported or
    even referenced by name in the firm package."""
    src = _all_firm_source().lower()
    for token in FORBIDDEN_BROKER_TOKENS:
        assert token not in src, (
            f"found forbidden brokerage token {token!r} in firm/ source")


def test_manager_module_hardcodes_broker_order_id_none():
    """Static check: broker_order_id is a source-level constant, not
    something derived from a model's output or any live client."""
    src = inspect.getsource(manager_mod)
    assert '"broker_order_id": None' in src
    assert '"simulated": True' in src


def test_manager_module_has_no_brokerage_client():
    """Static check: the manager node — the only place a paper_fill
    is produced — has no client object beyond the lazy LangChain LLM
    accessor, and no import of any order-routing library."""
    src = inspect.getsource(manager_mod)
    assert "requests" not in src
    assert "httpx" not in src
    assert "socket" not in src
    for token in FORBIDDEN_BROKER_TOKENS:
        assert token not in src.lower()


def test_paper_fill_always_has_none_broker_id_dynamically(monkeypatch):
    """Dynamic check: even if the manager's LLM tries to hand back
    something that looks like an order id or a live confirmation,
    the emitted paper_fill still has broker_order_id=None and
    simulated=True — those two keys are source-level literals in
    manager_node, never read from parsed model output."""
    monkeypatch.setattr(
        manager_mod, "_get_llm",
        lambda: manager_llm(action="BUY", size_pct=0.01))

    state = {
        "symbol": "SYNTH",
        "proposal": {
            "action": "BUY", "size_pct": 0.01,
            "stop_loss_pct": 0.02, "thesis": "t",
        },
        "risk": {
            "approved": True, "adjusted_size_pct": 0.01,
            "reasons": ["ok"],
        },
    }
    out = manager_mod.manager_node(state)
    fill = out["paper_fill"]
    assert fill["broker_order_id"] is None
    assert fill["simulated"] is True


def test_manager_hard_overrides_a_risk_veto_regardless_of_llm_output(
        monkeypatch):
    """Even if the manager's own LLM is adversarial and tries to
    approve a full-size BUY, a risk veto must force HOLD at
    size 0.0 in code — this is not negotiable by the model."""
    monkeypatch.setattr(
        manager_mod, "_get_llm",
        lambda: manager_llm(action="BUY", size_pct=0.05))

    state = {
        "symbol": "SYNTH",
        "proposal": {
            "action": "BUY", "size_pct": 0.05,
            "stop_loss_pct": 0.02, "thesis": "t",
        },
        "risk": {
            "approved": False, "adjusted_size_pct": 0.0,
            "reasons": ["drawdown limit breached"],
        },
    }
    out = manager_mod.manager_node(state)
    assert out["decision"]["action"] == "HOLD"
    assert out["decision"]["size_pct"] == 0.0
    assert out["paper_fill"]["action"] == "HOLD"
    assert out["paper_fill"]["broker_order_id"] is None
    assert out["paper_fill"]["simulated"] is True


def test_position_cap_is_clamped_by_code_min_not_by_the_prompt(
        monkeypatch):
    """The risk officer's LLM might hallucinate any adjusted size —
    including one far above the configured cap. risk_node must clamp
    it with min() in code, never trust the model's own arithmetic."""
    cap = risk_mod.POSITION_CAP
    monkeypatch.setattr(
        risk_mod, "_get_llm",
        lambda: risk_llm(approved=True, adjusted_size_pct=cap * 50))

    state = {
        "proposal": {
            "action": "BUY", "size_pct": cap * 50,
            "stop_loss_pct": 0.02, "thesis": "t",
        },
        "risk_revisions": 0,
    }
    out = risk_mod.risk_node(state)
    assert out["risk"]["adjusted_size_pct"] == cap
    assert out["risk"]["adjusted_size_pct"] <= cap


def test_risk_node_source_clamps_via_min_not_via_prompt_trust():
    """Static check that the clamp itself is a `min()` call over the
    module's POSITION_CAP constant, so this can never regress into
    "trust the LLM's own adjusted_size_pct"."""
    src = inspect.getsource(risk_mod.risk_node)
    assert "min(" in src
    assert "POSITION_CAP" in src


def test_risk_veto_zero_size_is_never_approved(monkeypatch):
    """A zero (or negative) adjusted size can never be `approved`,
    even if the model says so — risk_node itself must guard it."""
    monkeypatch.setattr(
        risk_mod, "_get_llm",
        lambda: risk_llm(approved=True, adjusted_size_pct=0.0))

    state = {
        "proposal": {
            "action": "BUY", "size_pct": 0.05,
            "stop_loss_pct": 0.02, "thesis": "t",
        },
        "risk_revisions": 0,
    }
    out = risk_mod.risk_node(state)
    assert out["risk"]["approved"] is False
