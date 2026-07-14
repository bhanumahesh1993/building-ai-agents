# tests/test_debate.py
"""The bull/bear debate must run for exactly `max_debate_rounds`
rounds, then hand off to the trader — never fewer, never more, and
never governed only by a prompt. `route_debate` in firm/graph.py is
the structural cap; these tests exercise it directly and then prove
it holds across a real (but fully faked) graph run."""
from __future__ import annotations

import uuid

from langgraph.types import Command

from firm.graph import build_graph, route_debate

from .conftest import patch_all_llms


def test_route_debate_continues_before_the_cap():
    state = {"debate_round": 0, "max_debate_rounds": 2}
    assert route_debate(state) == "bull"
    state = {"debate_round": 1, "max_debate_rounds": 2}
    assert route_debate(state) == "bull"


def test_route_debate_stops_at_the_cap():
    state = {"debate_round": 2, "max_debate_rounds": 2}
    assert route_debate(state) == "trader"
    # Never overruns even if debate_round somehow exceeds the cap.
    state = {"debate_round": 3, "max_debate_rounds": 2}
    assert route_debate(state) == "trader"


def test_full_graph_runs_exactly_max_debate_rounds(monkeypatch):
    """End to end: with max_debate_rounds=2, exactly 2 bull turns and
    2 bear turns are recorded, both sides speak every round, and the
    graph proceeds through trader -> risk -> manager to a paper_fill
    that never touches a broker."""
    patch_all_llms(
        monkeypatch, trader_size=0.02,
        risk_approved=True, risk_adjusted_size=0.02,
        manager_action="BUY", manager_size=0.02)

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke({
        "symbol": "SYNTH", "as_of": "2026-01-05",
        "debate_round": 0, "max_debate_rounds": 2,
        "risk_revisions": 0, "max_risk_revisions": 1,
    }, config=cfg)

    assert "__interrupt__" not in state
    assert state["debate_round"] == 2
    bull_turns = [t for t in state["debate"] if t["side"] == "bull"]
    bear_turns = [t for t in state["debate"] if t["side"] == "bear"]
    assert len(bull_turns) == 2
    assert len(bear_turns) == 2
    assert {t["round"] for t in bull_turns} == {1, 2}
    assert {t["round"] for t in bear_turns} == {1, 2}

    fill = state["paper_fill"]
    assert fill["broker_order_id"] is None
    assert fill["simulated"] is True


def test_full_graph_respects_a_single_round_cap(monkeypatch):
    """With max_debate_rounds=1, exactly one bull and one bear turn
    run before the trader — proving the cap is read from state, not
    hard-coded."""
    patch_all_llms(monkeypatch)

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke({
        "symbol": "SYNTH", "as_of": "2026-01-05",
        "debate_round": 0, "max_debate_rounds": 1,
        "risk_revisions": 0, "max_risk_revisions": 1,
    }, config=cfg)

    assert "__interrupt__" not in state
    assert state["debate_round"] == 1
    assert len(state["debate"]) == 2
    assert {t["side"] for t in state["debate"]} == {"bull", "bear"}
