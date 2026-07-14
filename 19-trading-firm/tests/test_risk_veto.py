# tests/test_risk_veto.py
"""The risk team is a veto gate: an unapproved proposal must route
back to the trader for revision, capped at max_risk_revisions, and
then to the manager which must force HOLD — never the trader's or
the model's original size. These tests exercise `route_risk`
directly and then the full (fully faked) graph."""
from __future__ import annotations

import uuid

from firm.graph import build_graph, route_risk

from .conftest import patch_all_llms


def test_route_risk_sends_approved_straight_to_manager():
    state = {"risk": {"approved": True}, "risk_revisions": 0,
             "max_risk_revisions": 1}
    assert route_risk(state) == "manager"


def test_route_risk_sends_unapproved_back_to_trader_until_cap():
    state = {"risk": {"approved": False}, "risk_revisions": 0,
             "max_risk_revisions": 1}
    assert route_risk(state) == "trader"


def test_route_risk_stops_revising_once_cap_is_reached():
    state = {"risk": {"approved": False}, "risk_revisions": 1,
              "max_risk_revisions": 1}
    assert route_risk(state) == "manager"


def test_full_graph_veto_forces_hold_after_max_revisions(monkeypatch):
    """A persistent veto (e.g. drawdown breach) must, after
    max_risk_revisions, still reach the manager and force HOLD at
    size 0.0 — never a BUY/SELL, and never the model's own size."""
    patch_all_llms(
        monkeypatch, trader_action="BUY", trader_size=0.05,
        risk_approved=False, risk_adjusted_size=0.0,
        manager_action="BUY", manager_size=0.05)

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke({
        "symbol": "SYNTH", "as_of": "2026-01-05",
        "debate_round": 0, "max_debate_rounds": 1,
        "risk_revisions": 0, "max_risk_revisions": 1,
    }, config=cfg)

    assert "__interrupt__" not in state
    assert state["risk"]["approved"] is False
    assert state["decision"]["action"] == "HOLD"
    assert state["decision"]["size_pct"] == 0.0
    assert state["paper_fill"]["action"] == "HOLD"
    assert state["paper_fill"]["broker_order_id"] is None


def test_full_graph_approved_risk_reaches_manager_with_adjusted_size(
        monkeypatch):
    """An approved, within-cap proposal must flow straight through:
    no revision loop, and the manager's decision is not forced."""
    patch_all_llms(
        monkeypatch, trader_action="BUY", trader_size=0.02,
        risk_approved=True, risk_adjusted_size=0.02,
        manager_action="BUY", manager_size=0.02)

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke({
        "symbol": "SYNTH", "as_of": "2026-01-05",
        "debate_round": 0, "max_debate_rounds": 1,
        "risk_revisions": 0, "max_risk_revisions": 1,
    }, config=cfg)

    assert "__interrupt__" not in state
    assert state["risk"]["approved"] is True
    assert state["risk_revisions"] == 0
    assert state["paper_fill"]["action"] == "BUY"
    assert state["paper_fill"]["size_pct"] == 0.02
    assert state["paper_fill"]["broker_order_id"] is None
    assert state["paper_fill"]["simulated"] is True


def test_large_paper_trade_pauses_for_human_confirmation(monkeypatch):
    """Above CONFIRM_ABOVE_PCT, the manager must pause at an
    interrupt — proving even an *approved* paper trade above the
    confirmation threshold cannot silently fill, and declining must
    force HOLD rather than ever reaching a broker."""
    from firm.nodes import manager as manager_mod
    from langgraph.types import Command

    big_size = manager_mod.CONFIRM_ABOVE_PCT + 0.02
    patch_all_llms(
        monkeypatch, trader_action="BUY", trader_size=big_size,
        risk_approved=True, risk_adjusted_size=big_size,
        manager_action="BUY", manager_size=big_size)

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke({
        "symbol": "SYNTH", "as_of": "2026-01-05",
        "debate_round": 0, "max_debate_rounds": 1,
        "risk_revisions": 0, "max_risk_revisions": 1,
    }, config=cfg)

    assert "__interrupt__" in state
    gate = state["__interrupt__"][0].value
    assert gate["symbol"] == "SYNTH"

    declined = graph.invoke(
        Command(resume={"confirmed": False}), config=cfg)
    assert declined["paper_fill"]["action"] == "HOLD"
    assert declined["paper_fill"]["size_pct"] == 0.0
    assert declined["paper_fill"]["broker_order_id"] is None
