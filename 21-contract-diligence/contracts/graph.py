# contracts/graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, interrupt
from langgraph.checkpoint.memory import InMemorySaver

from .extract import extract_node
from .ingest import load_contracts
from .memo import memo_node
from .playbook import playbook_node
from .redline import redline_node
from .risk_workers import risk_node
from .state import DDState

GROUND_ABOVE = ("medium", "high")


def ingest_node(state: DDState) -> dict:
    """Load and parse every file in the matter folder."""
    return {"contracts": load_contracts(state["doc_folder"])}


def fan_out_risk(state: DDState):
    """One specialist worker per distinct clause type."""
    by_type: dict[str, list] = {}
    for c in state["clauses"]:
        by_type.setdefault(c["clause_type"], []).append(c)
    return [
        Send("risk", {"clause_type": t, "clauses": cs})
        for t, cs in by_type.items()
    ]


def risk_barrier(state: DDState) -> dict:
    """Barrier: waits for every clause-type specialist
    before anything downstream decides what to ground.
    A conditional edge attached directly to `risk` would
    fire once per parallel instance -- this single node
    guarantees it fires exactly once, on merged state."""
    return {}


def fan_out_playbook(state: DDState):
    """One grounding call per flag worth grounding."""
    by_id = {c["clause_id"]: c for c in state["clauses"]}
    sends = [
        Send("playbook", {
            "flag": f, "clause": by_id[f["clause_id"]],
            "jurisdiction": state.get("jurisdiction", ""),
        })
        for f in state["flags"]
        if f["severity"] in GROUND_ABOVE
    ]
    return sends or ["redline"]


def attorney_gate(state: DDState) -> dict:
    """Pause: an attorney must sign off before delivery."""
    decision = interrupt({
        "memo": state["memo"],
        "flag_count": len(state.get("grounded", [])),
    })
    return {"reviewed": bool(decision.get("approved"))}


def build_graph(checkpointer=None):
    g = StateGraph(DDState)
    g.add_node("ingest", ingest_node)
    g.add_node("extract", extract_node)
    g.add_node("risk", risk_node)
    g.add_node("risk_barrier", risk_barrier)
    g.add_node("playbook", playbook_node)
    g.add_node("redline", redline_node)
    g.add_node("memo", memo_node)
    g.add_node("attorney_gate", attorney_gate)

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "extract")
    g.add_conditional_edges(
        "extract", fan_out_risk, ["risk"])
    g.add_edge("risk", "risk_barrier")
    g.add_conditional_edges(
        "risk_barrier", fan_out_playbook,
        ["playbook", "redline"])
    g.add_edge("playbook", "redline")
    g.add_edge("redline", "memo")
    g.add_edge("memo", "attorney_gate")
    g.add_edge("attorney_gate", END)

    cp = checkpointer or InMemorySaver()
    return g.compile(checkpointer=cp)
