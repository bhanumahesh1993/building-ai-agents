# triage/graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import InMemorySaver

from .state import TriageState
from .nodes.normalize import normalize_node
from .nodes.enrich import enrich_node
from .nodes.correlate import correlate_node
from .nodes.verdict import verdict_node
from .nodes.respond import respond_node


def fan_out(state: TriageState):
    """Spawn one worker per enrichment kind, parallel."""
    return [
        Send("enrich", {"alert": state["alert"],
                          "kind": k})
        for k in ("asset", "user", "intel")
    ]


def build_graph(checkpointer=None):
    g = StateGraph(TriageState)
    g.add_node("normalize", normalize_node)
    g.add_node("enrich", enrich_node)
    g.add_node("correlate", correlate_node)
    g.add_node("verdict", verdict_node)
    g.add_node("respond", respond_node)

    g.add_edge(START, "normalize")
    g.add_conditional_edges(
        "normalize", fan_out, ["enrich"])
    g.add_edge("enrich", "correlate")
    g.add_edge("correlate", "verdict")
    g.add_edge("verdict", "respond")
    g.add_edge("respond", END)

    cp = checkpointer or InMemorySaver()
    return g.compile(checkpointer=cp)
