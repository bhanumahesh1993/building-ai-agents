# support/graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from .state import TicketState
from .nodes.classify import classify_node
from .nodes.retrieve import retrieve_node
from .nodes.answer import answer_node
from .nodes.escalate import escalate_node


def resolve_node(state: TicketState) -> dict:
    """Mark a grounded answer as deflected."""
    return {
        "resolution": "deflected",
        "events": [{"node": "resolve",
                    "resolution": "deflected"}],
    }


def route_after_classify(state: TicketState) -> str:
    """Off-KB categories and low confidence skip search."""
    if state["category"] in ("feature_request", "abuse"):
        return "escalate"
    if state["confidence"] < 0.5:
        return "escalate"
    return "retrieve"


def route_after_answer(state: TicketState) -> str:
    """Grounded-or-escalate: never let a guess ship."""
    if state.get("grounded"):
        return "resolve"
    return "escalate"


def build_graph(checkpointer=None):
    g = StateGraph(TicketState)
    g.add_node("classify", classify_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("answer", answer_node)
    g.add_node("escalate", escalate_node)
    g.add_node("resolve", resolve_node)

    g.add_edge(START, "classify")
    g.add_conditional_edges(
        "classify", route_after_classify,
        ["retrieve", "escalate"])
    g.add_edge("retrieve", "answer")
    g.add_conditional_edges(
        "answer", route_after_answer,
        ["resolve", "escalate"])
    g.add_edge("resolve", END)
    g.add_edge("escalate", END)

    cp = checkpointer or InMemorySaver()
    return g.compile(checkpointer=cp)
