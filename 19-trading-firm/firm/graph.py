# firm/graph.py
from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from .nodes.analysts import analyst_node
from .nodes.debate import bear_node, bull_node
from .nodes.manager import manager_node
from .nodes.risk import risk_node
from .nodes.trader import trader_node
from .state import FirmState

ANALYST_KINDS = ["fundamental", "technical",
                 "sentiment", "news"]


def fan_out_analysts(state: FirmState):
    """Spawn one analyst per kind, in parallel."""
    return [
        Send("analyst", {
            "kind": k, "symbol": state["symbol"],
            "as_of": state["as_of"],
        })
        for k in ANALYST_KINDS
    ]


def route_debate(state: FirmState):
    """Loop bull/bear for max_debate_rounds, then trade."""
    if state["debate_round"] < state["max_debate_rounds"]:
        return "bull"
    return "trader"


def route_risk(state: FirmState):
    """Veto gate: approved -> manager; else revise, capped."""
    if state["risk"]["approved"]:
        return "manager"
    if state["risk_revisions"] < state["max_risk_revisions"]:
        return "trader"
    return "manager"


def build_graph(checkpointer=None):
    g = StateGraph(FirmState)
    g.add_node("analyst", analyst_node)
    g.add_node("bull", bull_node)
    g.add_node("bear", bear_node)
    g.add_node("trader", trader_node)
    g.add_node("risk", risk_node)
    g.add_node("manager", manager_node)

    g.add_conditional_edges(
        START, fan_out_analysts, ["analyst"])
    g.add_edge("analyst", "bull")
    g.add_edge("bull", "bear")
    g.add_conditional_edges(
        "bear", route_debate, ["bull", "trader"])
    g.add_edge("trader", "risk")
    g.add_conditional_edges(
        "risk", route_risk, ["trader", "manager"])
    g.add_edge("manager", END)

    cp = checkpointer or InMemorySaver()
    return g.compile(checkpointer=cp)
