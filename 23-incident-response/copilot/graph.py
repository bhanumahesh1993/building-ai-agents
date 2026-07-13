# copilot/graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import InMemorySaver

from .state import IncidentState
from .nodes.triage import triage_node
from .nodes.investigate import investigate_node
from .nodes.root_cause import root_cause_node
from .nodes.remediate import remediate_node


def fan_out(state: IncidentState):
    """Spawn one worker per investigation kind."""
    return [
        Send("investigate",
             {"alert": state["alert"], "kind": k})
        for k in ("logs", "metrics", "deploys",
                   "dependencies")
    ]


def build_graph(checkpointer=None):
    g = StateGraph(IncidentState)
    g.add_node("triage", triage_node)
    g.add_node("investigate", investigate_node)
    g.add_node("root_cause", root_cause_node)
    g.add_node("remediate", remediate_node)

    g.add_edge(START, "triage")
    g.add_conditional_edges(
        "triage", fan_out, ["investigate"])
    g.add_edge("investigate", "root_cause")
    g.add_edge("root_cause", "remediate")
    g.add_edge("remediate", END)

    cp = checkpointer or InMemorySaver()
    return g.compile(checkpointer=cp)
