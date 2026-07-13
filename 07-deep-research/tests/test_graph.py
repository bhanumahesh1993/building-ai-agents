# tests/test_graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Send

from research.state import ReportState


def _fake_plan(state: ReportState) -> dict:
    return {"plan": [
        {"topic": "a", "goal": "g"},
        {"topic": "b", "goal": "g"},
    ], "loops": 0, "max_loops": 1}


def _fake_worker(state) -> dict:
    t = state["task"]
    return {"findings": [{
        "topic": t["topic"],
        "summary": "s",
        "sources": [{"url": "u", "title": "t"}],
    }]}


def _fan(state: ReportState):
    return [Send("research",
                 {"task": t, "question": "q"})
            for t in state["plan"]]


def _build():
    g = StateGraph(ReportState)
    g.add_node("plan", _fake_plan)
    g.add_node("research", _fake_worker)
    g.add_edge(START, "plan")
    g.add_conditional_edges(
        "plan", _fan, ["research"])
    g.add_edge("research", END)
    return g.compile(checkpointer=InMemorySaver())


def test_fan_out_merges_findings():
    graph = _build()
    cfg = {"configurable": {"thread_id": "t1"}}
    out = graph.invoke({"question": "q"}, config=cfg)
    # Two workers fanned out and both merged in.
    assert len(out["findings"]) == 2
    topics = {f["topic"] for f in out["findings"]}
    assert topics == {"a", "b"}
