# tests/test_graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Send

from contracts.state import DDState


def _fake_extract(state: DDState) -> dict:
    return {"clauses": [
        {"clause_id": "a", "contract_id": "c1",
         "clause_type": "indemnification",
         "heading": "H", "text": "indemnify fully"},
        {"clause_id": "b", "contract_id": "c1",
         "clause_type": "termination",
         "heading": "H", "text": "terminate anytime"},
    ]}


def _fake_risk(state) -> dict:
    ctype = state["clause_type"]
    return {"flags": [{
        "clause_id": state["clauses"][0]["clause_id"],
        "clause_type": ctype, "severity": "high",
        "quote": state["clauses"][0]["text"],
        "rationale": "r",
    }]}


def _fan_risk(state: DDState):
    by_type: dict[str, list] = {}
    for c in state["clauses"]:
        by_type.setdefault(c["clause_type"], []).append(c)
    return [Send("risk", {"clause_type": t, "clauses": cs})
            for t, cs in by_type.items()]


def _build():
    g = StateGraph(DDState)
    g.add_node("extract", _fake_extract)
    g.add_node("risk", _fake_risk)
    g.add_edge(START, "extract")
    g.add_conditional_edges("extract", _fan_risk, ["risk"])
    g.add_edge("risk", END)
    return g.compile(checkpointer=InMemorySaver())


def test_fan_out_by_type_merges_flags():
    graph = _build()
    cfg = {"configurable": {"thread_id": "t1"}}
    out = graph.invoke({"matter_id": "m1"}, config=cfg)
    # Two clause types fanned out and both merged in.
    assert len(out["flags"]) == 2
    types = {f["clause_type"] for f in out["flags"]}
    assert types == {"indemnification", "termination"}
