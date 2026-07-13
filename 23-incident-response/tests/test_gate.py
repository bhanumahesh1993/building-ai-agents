# tests/test_gate.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

from copilot.state import IncidentState


def _fake_root_cause(state: IncidentState) -> dict:
    return {"root_cause": {
        "hypothesis": "h", "confidence": 0.9,
        "evidence": ["e"],
        "category": "deploy_regression"}}


def _fake_remediate(state: IncidentState) -> dict:
    decision = interrupt(
        {"action": "rollback_deploy"})
    if not decision.get("approved", False):
        return {"resolution": "escalated"}
    return {"resolution": "remediated"}


def _build():
    g = StateGraph(IncidentState)
    g.add_node("root_cause", _fake_root_cause)
    g.add_node("remediate", _fake_remediate)
    g.add_edge(START, "root_cause")
    g.add_edge("root_cause", "remediate")
    g.add_edge("remediate", END)
    return g.compile(checkpointer=InMemorySaver())


def test_declined_approval_never_remediates():
    """A human decline must never reach 'remediated'."""
    graph = _build()
    cfg = {"configurable": {"thread_id": "t1"}}
    graph.invoke({}, config=cfg)
    out = graph.invoke(
        Command(resume={"approved": False}),
        config=cfg)
    assert out["resolution"] == "escalated"


def test_root_cause_holds_no_destructive_names():
    """Static check: the reasoning step's own
    source never names a destructive action."""
    import copilot.nodes.root_cause as rc_mod
    src = open(rc_mod.__file__).read()
    assert "rollback_deploy" not in src
    assert "restart_service" not in src
    assert "scale_service" not in src
