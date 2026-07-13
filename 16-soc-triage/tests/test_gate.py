# tests/test_gate.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

from triage.state import TriageState


def _fake_verdict(state: TriageState) -> dict:
    return {"verdict": {
        "label": "true_positive", "confidence": 0.9,
        "evidence": ["e"],
        "recommended_action": "disable_account"}}


def _fake_respond(state: TriageState) -> dict:
    decision = interrupt({"action": "disable_account"})
    if not decision.get("approved", False):
        return {"resolution": "escalated"}
    return {"resolution": "contained"}


def _build():
    g = StateGraph(TriageState)
    g.add_node("verdict", _fake_verdict)
    g.add_node("respond", _fake_respond)
    g.add_edge(START, "verdict")
    g.add_edge("verdict", "respond")
    g.add_edge("respond", END)
    return g.compile(checkpointer=InMemorySaver())


def test_declined_approval_never_contains():
    """A human decline must never reach 'contained'."""
    graph = _build()
    cfg = {"configurable": {"thread_id": "t1"}}
    graph.invoke({}, config=cfg)
    out = graph.invoke(
        Command(resume={"approved": False}),
        config=cfg)
    assert out["resolution"] == "escalated"


def test_verdict_module_holds_no_destructive_names():
    """Static check: the reasoning step's own source
    never names a destructive action directly."""
    import triage.nodes.verdict as verdict_mod
    src = open(verdict_mod.__file__).read()
    assert "disable_account" not in src
    assert "isolate_host" not in src
